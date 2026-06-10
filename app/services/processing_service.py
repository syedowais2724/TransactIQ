"""
Shared transaction processing helpers used by Celery and local mode.
"""
import logging
import re
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.job_summary import JobSummary
from app.models.transaction import Transaction
from app.services.gemini_service import GeminiService
from app.utils.data_cleaner import FALLBACK_CATEGORY, MISSING_CATEGORY, normalize_category_value

logger = logging.getLogger(__name__)

MERCHANT_CATEGORY_RULES = [
    (re.compile(r"\b(zomato|swiggy|starbucks|mcdonald|domino|pizza|cafe|restaurant|grocery|bigbasket)\b", re.I), "Food"),
    (re.compile(r"\b(ola|uber|rapido|metro|parking|fuel|petrol|shell|bpcl|hpcl)\b", re.I), "Transport"),
    (re.compile(r"\b(irctc|makemytrip|goibibo|cleartrip|indigo|air india|vistara|hotel|booking)\b", re.I), "Travel"),
    (re.compile(r"\b(netflix|spotify|bookmyshow|prime video|hotstar|youtube|cinema|movie|gaming)\b", re.I), "Entertainment"),
    (re.compile(r"\b(amazon|flipkart|myntra|ajio|nykaa|walmart|target|store|retail|electronics)\b", re.I), "Shopping"),
    (re.compile(r"\b(electric|electricity|water|broadband|internet|airtel|jio|vi |vodafone|utility|gas bill)\b", re.I), "Utilities"),
    (re.compile(r"\b(atm|cash withdrawal|cash advance)\b", re.I), "Cash Withdrawal"),
]


def classify_by_rules(row: pd.Series) -> str | None:
    """Return a high-confidence category from merchant/notes text."""
    merchant = str(row.get("merchant") or "")
    notes = str(row.get("notes") or "")
    haystack = f"{merchant} {notes}".strip()

    for pattern, category in MERCHANT_CATEGORY_RULES:
        if pattern.search(haystack):
            logger.info("Rule classified txn_id=%s merchant=%s category=%s", row.get("txn_id"), merchant, category)
            return category
    return None


def classify_missing_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify only temporary missing-category rows and replace every marker.
    Gemini failures fall back to "Other" so charts never show placeholders.
    """
    df["llm_category"] = None
    df["llm_raw_response"] = None
    df["llm_failed"] = False

    missing_mask = df["category"].eq(MISSING_CATEGORY)
    logger.info("===== CATEGORY CLASSIFICATION START =====")
    logger.info("Total rows: %s", len(df))
    logger.info("Rows with missing category before rules: %s", int(missing_mask.sum()))

    rule_count = 0
    for idx, row in df[missing_mask].iterrows():
        rule_category = classify_by_rules(row)
        if rule_category:
            df.at[idx, "category"] = rule_category
            df.at[idx, "llm_category"] = rule_category
            df.at[idx, "llm_raw_response"] = "pre_classification_rule"
            df.at[idx, "llm_failed"] = False
            rule_count += 1

    missing_mask = df["category"].eq(MISSING_CATEGORY)
    missing_df = df[missing_mask]
    logger.info("Rows classified by deterministic rules: %s", rule_count)
    logger.info("Rows sent to Gemini: %s", len(missing_df))

    if missing_df.empty:
        df["category"] = df["category"].apply(lambda value: normalize_category_value(value, FALLBACK_CATEGORY))
        logger.info("No missing categories to classify")
        return df

    transactions = missing_df[["txn_id", "merchant", "amount", "notes"]].to_dict("records")

    try:
        gemini_service = GeminiService()
        results = gemini_service.classify_categories_batch(transactions)
        logger.info("Gemini responses received: %s", len(results))
        for result in results[:5]:
            logger.info(
                "Gemini response sample: txn_id=%s category=%s confidence=%s success=%s",
                result.get("txn_id"),
                result.get("category"),
                result.get("confidence"),
                result.get("success"),
            )

        results_map = {str(result["txn_id"]): result for result in results}
        updated_count = 0

        for idx, row in df[missing_mask].iterrows():
            txn_id = str(row["txn_id"])
            result = results_map.get(txn_id)

            if result:
                category = normalize_category_value(result.get("category"), FALLBACK_CATEGORY)
                if category == MISSING_CATEGORY:
                    category = FALLBACK_CATEGORY
                success = bool(result.get("success"))
                df.at[idx, "llm_category"] = category
                confidence = float(result.get("confidence", 0.0) or 0.0)
                df.at[idx, "llm_raw_response"] = f"confidence={confidence:.2f}; {result.get('raw_response', '')}"
                df.at[idx, "llm_failed"] = not success
                if category == FALLBACK_CATEGORY and confidence < 0.35:
                    logger.info("Low-confidence Gemini fallback for txn_id=%s merchant=%s", txn_id, row.get("merchant"))
            else:
                category = FALLBACK_CATEGORY
                df.at[idx, "llm_failed"] = True
                df.at[idx, "llm_raw_response"] = "Missing Gemini response"

            df.at[idx, "category"] = category
            updated_count += 1

        logger.info("Rows updated successfully after Gemini classification: %s", updated_count)

    except Exception as exc:
        logger.error("Gemini classification failed completely: %s", exc, exc_info=True)
        df.loc[missing_mask, "category"] = FALLBACK_CATEGORY
        df.loc[missing_mask, "llm_failed"] = True
        df.loc[missing_mask, "llm_raw_response"] = f"Error: {exc}"
        logger.warning("Rows updated successfully with fallback category '%s': %s", FALLBACK_CATEGORY, len(missing_df))

    df["category"] = df["category"].apply(lambda value: normalize_category_value(value, FALLBACK_CATEGORY))
    df.loc[df["category"].eq(MISSING_CATEGORY), "category"] = FALLBACK_CATEGORY

    logger.info("===== FINAL CATEGORY DISTRIBUTION =====")
    for category, count in df["category"].value_counts().items():
        logger.info("  %s: %s (%.1f%%)", category, count, (count / len(df)) * 100 if len(df) else 0)

    return df


def store_transactions(db: Session, job_id: int, df: pd.DataFrame) -> None:
    """Store processed transactions in database."""
    transactions = []

    for _, row in df.iterrows():
        transaction = Transaction(
            job_id=job_id,
            txn_id=str(row["txn_id"]),
            date=row["date"],
            merchant=str(row["merchant"]),
            amount=float(row["amount"]),
            currency=str(row["currency"]),
            status=str(row["status"]),
            category=normalize_category_value(row["category"], FALLBACK_CATEGORY),
            account_id=str(row["account_id"]),
            notes=row.get("notes"),
            is_anomaly=bool(row["is_anomaly"]),
            anomaly_reason=row.get("anomaly_reason"),
            llm_category=row.get("llm_category"),
            llm_raw_response=row.get("llm_raw_response"),
            llm_failed=bool(row.get("llm_failed", False)),
        )
        transactions.append(transaction)

    db.bulk_save_objects(transactions)
    db.commit()
    logger.info("Stored %s transactions for job %s", len(transactions), job_id)


def build_fallback_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Create a deterministic summary when Gemini is unavailable."""
    spend_by_currency = {str(k): float(v) for k, v in df.groupby("currency")["amount"].sum().to_dict().items()}
    top_merchants = [
        {"merchant": str(merchant), "amount": float(amount)}
        for merchant, amount in df.groupby("merchant")["amount"].sum().nlargest(3).items()
    ]
    anomaly_count = int(df["is_anomaly"].sum()) if "is_anomaly" in df else 0
    total_rows = max(len(df), 1)
    anomaly_rate = anomaly_count / total_rows
    risk_level = "high" if anomaly_rate > 0.15 else "medium" if anomaly_rate >= 0.05 else "low"
    top_categories = list(df.groupby("category")["amount"].sum().sort_values(ascending=False).head(2).index)

    if top_categories:
        category_text = " and ".join(str(category) for category in top_categories)
        first_sentence = f"Most spending occurred in {category_text}."
    else:
        first_sentence = "Spending was distributed across the uploaded transactions."

    narrative = f"{first_sentence} {anomaly_count} anomalous transactions were detected. Overall risk level is {risk_level.title()}."

    return {
        "total_spend_by_currency": spend_by_currency,
        "top_3_merchants": top_merchants,
        "anomaly_count": anomaly_count,
        "narrative": narrative,
        "risk_level": risk_level,
    }


def generate_and_store_summary(db: Session, job_id: int, df: pd.DataFrame) -> None:
    """Generate AI summary with deterministic fallback and store it."""
    summary_data = None

    try:
        gemini_service = GeminiService()
        summary_data = gemini_service.generate_summary(df)
    except Exception as exc:
        logger.error("AI summary generation failed, using fallback: %s", exc, exc_info=True)

    if not summary_data:
        summary_data = build_fallback_summary(df)

    spend = summary_data.get("total_spend_by_currency", {})
    summary = JobSummary(
        job_id=job_id,
        total_spend_inr=float(spend.get("INR", 0) or 0),
        total_spend_usd=float(spend.get("USD", 0) or 0),
        top_merchants=summary_data.get("top_3_merchants", []),
        anomaly_count=int(summary_data.get("anomaly_count", 0) or 0),
        narrative=summary_data.get("narrative") or build_fallback_summary(df)["narrative"],
        risk_level=(summary_data.get("risk_level") or "low").lower(),
    )

    db.add(summary)
    db.commit()
    logger.info("Stored summary for job %s", job_id)


def get_category_breakdown(db: Session, job_id: int) -> List[Dict[str, Any]]:
    """Aggregate final cleaned categories with normalized casing."""
    rows = db.query(
        Transaction.category,
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.amount).label("total_amount"),
    ).filter(Transaction.job_id == job_id).group_by(Transaction.category).all()

    merged: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        category = normalize_category_value(row.category, FALLBACK_CATEGORY)
        if category == MISSING_CATEGORY:
            category = FALLBACK_CATEGORY
        current = merged.setdefault(category, {"category": category, "count": 0, "total_amount": 0.0})
        current["count"] += int(row.count or 0)
        current["total_amount"] += float(row.total_amount or 0)

    return sorted(merged.values(), key=lambda item: item["total_amount"], reverse=True)
