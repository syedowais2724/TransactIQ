"""
Data cleaning utilities for CSV processing.
Handles date normalization, currency cleaning, and duplicate removal.
"""
import pandas as pd
from datetime import datetime
from typing import Tuple, Any
import logging
import re

logger = logging.getLogger(__name__)

MISSING_CATEGORY = "__MISSING__"
FALLBACK_CATEGORY = "Other"


def clean_amount(amount_str: Any) -> float:
    """Public helper for tests and services."""
    return DataCleaner.clean_amount(amount_str)


def normalize_category_value(value: Any, missing_token: str = MISSING_CATEGORY) -> str:
    """Normalize category casing while preserving a marker for AI classification."""
    if pd.isna(value):
        return missing_token

    category = str(value).strip()
    missing_values = {"", "nan", "none", "null", "undefined", "uncategorised", "uncategorized"}
    if category.lower() in missing_values:
        return missing_token

    normalized = re.sub(r"\s+", " ", category).strip()
    known = {
        "food": "Food",
        "shopping": "Shopping",
        "travel": "Travel",
        "transport": "Transport",
        "utilities": "Utilities",
        "cash withdrawal": "Cash Withdrawal",
        "entertainment": "Entertainment",
        "other": "Other",
    }
    return known.get(normalized.lower(), normalized.title())


class DataCleaner:
    """Handles data cleaning operations on transaction DataFrames."""

    @staticmethod
    def clean_amount(amount_str) -> float:
        """
        ROBUST amount parser that handles all edge cases.
        
        Examples:
        - "$4,627.78" -> 4627.78
        - "₹12,500" -> 12500.0
        - " 9,876.50 " -> 9876.50
        - "1234.56" -> 1234.56
        - "€1.234,56" (European format) -> 1234.56
        
        This function is critical for accurate spend calculations!
        """
        if pd.isna(amount_str):
            logger.warning("Encountered NaN amount, returning 0.0")
            return 0.0
        
        # Convert to string and strip whitespace
        amount_str = str(amount_str).strip()
        
        if not amount_str:
            return 0.0
        
        # Remove all currency symbols: $, ₹, €, £, ¥, etc.
        amount_str = re.sub(r'[^\d,.\-\s]', '', amount_str)
        
        # Remove all spaces
        amount_str = amount_str.replace(' ', '')
        
        # Handle European format (1.234,56 -> 1234.56)
        # If there's both comma and dot, check which is the decimal separator
        if ',' in amount_str and '.' in amount_str:
            # If dot comes before comma, it's likely European format (1.234,56)
            if amount_str.rfind('.') < amount_str.rfind(','):
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                # Otherwise US format ($1,234.56)
                amount_str = amount_str.replace(',', '')
        elif ',' in amount_str:
            # Check if comma is decimal separator or thousands separator
            # If there are digits after comma, it might be decimal (European)
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Likely European decimal: 1234,56
                amount_str = amount_str.replace(',', '.')
            else:
                # Likely thousands separator: 1,234,567
                amount_str = amount_str.replace(',', '')
        
        # Final cleanup and conversion
        amount_str = amount_str.strip()
        
        try:
            parsed = float(amount_str)
            if parsed < 0:
                logger.warning(f"Negative amount detected: {parsed}, using absolute value")
                parsed = abs(parsed)
            return parsed
        except ValueError:
            logger.error(f"Could not parse amount: '{amount_str}', returning 0.0")
            return 0.0

    @staticmethod
    def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize various date formats to ISO format (YYYY-MM-DD).
        Handles formats like: DD/MM/YYYY, MM-DD-YYYY, DD-MMM-YYYY, etc.
        """
        def parse_date(date_str):
            if pd.isna(date_str):
                return None
            
            # Try common date formats
            formats = [
                '%Y-%m-%d',      # ISO format
                '%d/%m/%Y',      # DD/MM/YYYY
                '%m/%d/%Y',      # MM/DD/YYYY
                '%d-%m-%Y',      # DD-MM-YYYY
                '%m-%d-%Y',      # MM-DD-YYYY
                '%d-%b-%Y',      # DD-MMM-YYYY
                '%d %b %Y',      # DD MMM YYYY
                '%Y/%m/%d',      # YYYY/MM/DD
                '%d.%m.%Y',      # DD.MM.YYYY
                '%Y%m%d',        # YYYYMMDD
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(date_str).strip(), fmt).date()
                except (ValueError, TypeError):
                    continue
            
            # If none of the formats work, log warning and return None
            logger.warning(f"Could not parse date: {date_str}")
            return None
        
        df['date'] = df['date'].apply(parse_date)
        
        # Count and log invalid dates
        invalid_dates = df['date'].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Found {invalid_dates} invalid dates, removing those rows")
        
        # Remove rows with invalid dates
        df = df.dropna(subset=['date'])
        return df

    @staticmethod
    def generate_transaction_id(index: int) -> str:
        """
        Generate fallback transaction ID.
        Format: AUTO_TXN_0001, AUTO_TXN_0002, etc.
        """
        return f"AUTO_TXN_{index:04d}"

    @staticmethod
    def normalize_transaction_ids(df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure all transactions have valid IDs.
        Generate fallback IDs for missing values.
        NEVER expose NaN, null, or undefined to frontend!
        """
        missing_tokens = {'', 'nan', 'none', 'null', 'undefined', 'missing_id'}
        txn_series = df['txn_id'].astype(str).str.strip()
        missing_ids = df['txn_id'].isna() | txn_series.str.lower().isin(missing_tokens)
        missing_count = missing_ids.sum()
        
        if missing_count > 0:
            logger.warning(f"Found {missing_count} missing transaction IDs, generating fallbacks")
            
            sequence = 1
            used_ids = set(txn_series[~missing_ids].astype(str))
            for idx in df[missing_ids].index:
                candidate = DataCleaner.generate_transaction_id(sequence)
                while candidate in used_ids:
                    sequence += 1
                    candidate = DataCleaner.generate_transaction_id(sequence)
                df.at[idx, 'txn_id'] = candidate
                used_ids.add(candidate)
                sequence += 1
        
        # Ensure all IDs are strings and not NaN
        df['txn_id'] = df['txn_id'].astype(str).str.strip()
        
        seen = set()
        duplicate_count = 0
        sequence = 1
        for idx, txn_id in df['txn_id'].items():
            normalized = str(txn_id).strip()
            if normalized in seen:
                duplicate_count += 1
                candidate = DataCleaner.generate_transaction_id(sequence)
                while candidate in seen:
                    sequence += 1
                    candidate = DataCleaner.generate_transaction_id(sequence)
                df.at[idx, 'txn_id'] = candidate
                seen.add(candidate)
                sequence += 1
            else:
                seen.add(normalized)

        if duplicate_count:
            logger.warning(f"Replaced {duplicate_count} duplicate transaction IDs with fallbacks")
        
        return df

    @staticmethod
    def apply_amount_cleaning(df: pd.DataFrame) -> pd.DataFrame:
        """Apply robust amount cleaning to DataFrame."""
        logger.info(f"Cleaning amounts for {len(df)} rows...")
        df['amount'] = df['amount'].apply(DataCleaner.clean_amount)
        
        # Log statistics
        total = df['amount'].sum()
        mean = df['amount'].mean()
        median = df['amount'].median()
        logger.info(f"Amount statistics - Total: {total:.2f}, Mean: {mean:.2f}, Median: {median:.2f}")
        
        return df

    @staticmethod
    def normalize_status(df: pd.DataFrame) -> pd.DataFrame:
        """Convert status values to uppercase."""
        df['status'] = df['status'].fillna('UNKNOWN').str.upper().str.strip()
        return df

    @staticmethod
    def normalize_currency(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize currency casing (e.g., usd -> USD)."""
        df['currency'] = df['currency'].fillna('INR').str.upper().str.strip()
        return df

    @staticmethod
    def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
        """
        CRITICAL: Mark missing categories but DON'T pre-fill!
        Let AI classification happen first.
        Only use 'Uncategorised' as a temporary marker.
        """
        # Store original categories
        df['original_category'] = df['category']
        
        # Mark missing/empty as temporary placeholder and normalize provided labels.
        df['category'] = df['category'].apply(normalize_category_value)
        
        missing_count = (df['category'] == MISSING_CATEGORY).sum()
        logger.info(f"Found {missing_count} rows with missing categories (will be classified by AI)")
        
        return df

    @staticmethod
    def validate_required_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate that all required columns exist.
        Fill missing columns with defaults.
        """
        required_columns = {
            'txn_id': 'MISSING_ID',
            'date': None,  # Will be handled by date normalization
            'merchant': 'Unknown Merchant',
            'amount': 0.0,
            'currency': 'INR',
            'status': 'UNKNOWN',
            'category': MISSING_CATEGORY,
            'account_id': 'UNKNOWN_ACCOUNT',
            'notes': ''
        }
        
        for col, default in required_columns.items():
            if col not in df.columns:
                logger.warning(f"Column '{col}' missing, adding with default: {default}")
                df[col] = default
        
        return df

    @staticmethod
    def remove_invalid_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Remove rows with critical missing data.
        Log details about removed rows.
        """
        initial_count = len(df)
        
        # Remove rows with zero or negative amounts
        invalid_amounts = (df['amount'] <= 0)
        if invalid_amounts.any():
            logger.warning(f"Removing {invalid_amounts.sum()} rows with invalid amounts")
            df = df[~invalid_amounts]
        
        # Remove rows with missing merchants
        missing_merchants = df['merchant'].isna() | (df['merchant'] == '') | (df['merchant'] == 'nan')
        if missing_merchants.any():
            logger.warning(f"Removing {missing_merchants.sum()} rows with missing merchants")
            df = df[~missing_merchants]
        
        removed = initial_count - len(df)
        return df, removed

    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Remove exact duplicate rows based on key fields.
        Returns cleaned DataFrame and count of duplicates removed.
        """
        initial_count = len(df)
        
        # Consider duplicates based on: date, merchant, amount, account_id
        key_columns = ['date', 'merchant', 'amount', 'account_id']
        df = df.drop_duplicates(subset=key_columns, keep='first')
        
        duplicates_removed = initial_count - len(df)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate transactions")
        
        return df, duplicates_removed

    @classmethod
    def clean_dataframe(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """
        Apply all cleaning operations to the DataFrame.
        Returns cleaned DataFrame and statistics about the cleaning process.
        
        CRITICAL ORDER:
        1. Validate columns
        2. Normalize transaction IDs (prevent NaN exposure!)
        3. Clean amounts (proper comma/decimal handling!)
        4. Normalize dates
        5. Normalize other fields
        6. Mark missing categories (DON'T pre-fill!)
        7. Remove duplicates
        8. Remove invalid rows
        """
        initial_count = len(df)
        stats = {'initial_rows': initial_count}
        
        logger.info(f"Starting data cleaning on {initial_count} rows...")
        
        # Step 1: Validate columns
        df = cls.validate_required_columns(df)
        
        # Step 2: Fix transaction IDs FIRST (critical!)
        df = cls.normalize_transaction_ids(df)
        stats['txn_ids_generated'] = (df['txn_id'].str.startswith('AUTO_TXN_')).sum()
        
        # Step 3: Clean amounts with robust parser
        df = cls.apply_amount_cleaning(df)
        
        # Step 4: Normalize dates
        df = cls.normalize_dates(df)
        stats['after_date_cleaning'] = len(df)
        
        # Step 5: Normalize other fields
        df = cls.normalize_status(df)
        df = cls.normalize_currency(df)
        
        # Step 6: Mark missing categories (DON'T fill with "Uncategorised" yet!)
        df = cls.normalize_categories(df)
        stats['missing_categories'] = (df['category'] == MISSING_CATEGORY).sum()
        
        # Step 7: Remove duplicates
        df, duplicates = cls.remove_duplicates(df)
        stats['duplicates_removed'] = duplicates
        
        # Step 8: Remove invalid rows
        df, removed = cls.remove_invalid_rows(df)
        stats['invalid_rows_removed'] = removed
        
        stats['final_rows'] = len(df)
        
        logger.info(f"Data cleaning completed: {initial_count} -> {len(df)} rows")
        logger.info(f"  - Transaction IDs generated: {stats['txn_ids_generated']}")
        logger.info(f"  - Missing categories: {stats['missing_categories']}")
        logger.info(f"  - Duplicates removed: {stats['duplicates_removed']}")
        logger.info(f"  - Invalid rows removed: {stats['invalid_rows_removed']}")
        
        return df, stats
