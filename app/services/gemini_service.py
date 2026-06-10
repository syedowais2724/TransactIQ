"""
Gemini AI service for category classification and summary generation.
Implements retry logic with exponential backoff.
UPDATED: Using new google.genai package (old one deprecated).
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import json

# Try new API first, fall back to old if needed
try:
    from google import genai
    from google.genai import types
    NEW_API = True
    logger = logging.getLogger(__name__)
    logger.info("Using NEW google.genai API")
except ImportError:
    import google.generativeai as genai
    NEW_API = False
    logger = logging.getLogger(__name__)
    logger.warning("Using DEPRECATED google.generativeai API - please upgrade!")


class GeminiService:
    """Handles all Gemini AI API interactions."""
    
    # Valid transaction categories
    VALID_CATEGORIES = [
        "Food",
        "Shopping",
        "Travel",
        "Transport",
        "Utilities",
        "Cash Withdrawal",
        "Entertainment",
        "Other"
    ]
    
    def __init__(self):
        """Initialize Gemini API with API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        logger.info(f"Initializing Gemini with API key: {api_key[:15]}...")
        
        try:
            if NEW_API:
                # New API initialization
                self.client = genai.Client(api_key=api_key)
                self.model_name = 'gemini-2.0-flash-exp'  # Use latest model
                logger.info(f"✓ Gemini service initialized (NEW API, model: {self.model_name})")
            else:
                # Old API initialization (deprecated)
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✓ Gemini service initialized (OLD API, model: gemini-1.5-flash)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise
    
    def _retry_with_backoff(self, func, max_retries: int = 3) -> Tuple[Any, bool]:
        """
        Execute function with exponential backoff retry logic.
        Returns: (result, success_flag)
        """
        for attempt in range(max_retries):
            try:
                result = func()
                return result, True
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed: {str(e)}")
                    return None, False
        
        return None, False
    
    def _generate_content_new_api(self, prompt: str) -> str:
        """Generate content using NEW google.genai API."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text
    
    def _generate_content_old_api(self, prompt: str) -> str:
        """Generate content using OLD google.generativeai API."""
        response = self.model.generate_content(prompt)
        return response.text
    
    def _generate_content(self, prompt: str) -> str:
        """Unified content generation (handles both APIs)."""
        if NEW_API:
            return self._generate_content_new_api(prompt)
        else:
            return self._generate_content_old_api(prompt)
    
    def classify_categories_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify missing categories for multiple transactions in batches.
        Returns list of dicts with: txn_id, category, confidence, success, raw_response
        
        CRITICAL: This function MUST return a result for EVERY transaction!
        """
        if not transactions:
            logger.warning("No transactions to classify")
            return []
        
        logger.info(f"Classifying {len(transactions)} transactions in batches...")
        
        results = []
        batch_size = 10  # Smaller batches for better reliability
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(transactions)-1)//batch_size + 1} ({len(batch)} transactions)")
            batch_results = self._classify_batch(batch)
            results.extend(batch_results)
            
            # Small delay between batches to avoid rate limiting
            if i + batch_size < len(transactions):
                time.sleep(0.5)
        
        logger.info(f"Batch classification complete: {len(results)} results")
        return results
    
    def _classify_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify a single batch of transactions."""
        prompt = self._build_classification_prompt(batch)
        
        def api_call():
            response_text = self._generate_content(prompt)
            logger.info(f"Gemini classification raw response: {response_text[:500]}")
            return self._parse_classification_response(response_text, batch)
        
        results, success = self._retry_with_backoff(api_call)
        
        if not success or not results:
            # ALL transactions in batch failed - return fallback
            logger.error(f"Batch classification failed completely for {len(batch)} transactions")
            return [
                {
                    'txn_id': txn['txn_id'],
                    'category': 'Other',  # Fallback category
                    'confidence': 0.0,
                    'success': False,
                    'raw_response': 'Failed after retries'
                }
                for txn in batch
            ]
        
        return results
    
    def _build_classification_prompt(self, transactions: List[Dict[str, Any]]) -> str:
        """Build prompt for category classification."""
        categories_str = ", ".join(self.VALID_CATEGORIES)
        
        prompt = f"""You are a financial transaction categorization expert for an Indian fintech analytics dashboard.

Classify each transaction into ONE of these categories:
{categories_str}

Rules:
- Food: restaurants, cafes, groceries, food delivery
- Shopping: retail, online shopping, clothing, electronics
- Travel: flights, hotels, travel agencies
- Transport: taxis, ride-sharing, gas, parking, public transit
- Utilities: electricity, water, internet, phone bills
- Cash Withdrawal: ATM withdrawals, cash advances
- Entertainment: movies, games, streaming services, events
- Other: only when none of the above categories is a reasonable fit

Use merchant names, notes, and amount context. Prefer a specific category over Other when there is a recognizable merchant pattern.

Examples:
- Zomato, Swiggy, Starbucks, grocery stores -> Food
- Ola, Uber, Rapido, fuel, parking -> Transport
- IRCTC, MakeMyTrip, flights, hotels -> Travel
- Netflix, BookMyShow, Spotify, gaming -> Entertainment
- Amazon, Flipkart, Myntra, electronics stores -> Shopping
- Airtel, Jio, electricity, water, broadband -> Utilities
- ATM, cash withdrawal -> Cash Withdrawal

Transactions to classify:
"""
        
        for txn in transactions:
            notes = txn.get('notes', '') or 'N/A'
            prompt += f"\n- txn_id: {txn['txn_id']}, merchant: {txn['merchant']}, amount: {txn['amount']}, notes: {notes}"
        
        prompt += f"""

IMPORTANT: Return ONLY a JSON array, no additional text!
Format:
[
  {{"txn_id": "TXN001", "category": "Food", "confidence": 0.92}},
  {{"txn_id": "TXN002", "category": "Transport", "confidence": 0.86}}
]

JSON array:"""
        
        return prompt
    
    def _parse_classification_response(self, response_text: str, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse Gemini response and extract categories."""
        try:
            # Clean response
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])  # Remove first and last lines
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON
            classifications = json.loads(response_text)
            
            # Build results map
            results_map = {str(item.get('txn_id')): item for item in classifications}
            
            # Match with original batch and validate categories
            results = []
            for txn in batch:
                item = results_map.get(str(txn['txn_id']), {})
                category = item.get('category', 'Other')
                confidence = float(item.get('confidence', 0.0) or 0.0)
                
                # Validate category
                if category not in self.VALID_CATEGORIES:
                    logger.warning(f"Invalid category '{category}' for {txn['txn_id']}, using 'Other'")
                    category = 'Other'
                    confidence = 0.0

                results.append({
                    'txn_id': txn['txn_id'],
                    'category': category,
                    'confidence': max(0.0, min(confidence, 1.0)),
                    'success': True,
                    'raw_response': response_text[:500]  # Truncate for storage
                })
            
            logger.info(f"✓ Successfully parsed {len(results)} classifications")
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response_text[:200]}...")
            
            # Return fallback for all transactions
            return [
                {
                    'txn_id': txn['txn_id'],
                    'category': 'Other',
                    'confidence': 0.0,
                    'success': False,
                    'raw_response': response_text[:500]
                }
                for txn in batch
            ]
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return [
                {
                    'txn_id': txn['txn_id'],
                    'category': 'Other',
                    'confidence': 0.0,
                    'success': False,
                    'raw_response': f"Parse error: {str(e)}"
                }
                for txn in batch
            ]
    
    def generate_summary(self, transactions_df) -> Optional[Dict[str, Any]]:
        """
        Generate AI-powered summary report for all transactions.
        Returns dict with: total_spend_by_currency, top_3_merchants, anomaly_count, narrative, risk_level
        """
        logger.info("Generating AI summary...")
        prompt = self._build_summary_prompt(transactions_df)
        
        def api_call():
            response_text = self._generate_content(prompt)
            return self._parse_summary_response(response_text)
        
        summary, success = self._retry_with_backoff(api_call)
        
        if not success:
            logger.error("Failed to generate summary after retries")
            return None
        
        logger.info("✓ Summary generated successfully")
        return summary
    
    def _build_summary_prompt(self, df) -> str:
        """Build prompt for summary generation."""
        # Calculate statistics
        spend_by_currency = df.groupby('currency')['amount'].sum().to_dict()
        top_merchants = df.groupby('merchant')['amount'].sum().nlargest(3).to_dict()
        anomaly_count = int(df['is_anomaly'].sum())
        total_transactions = len(df)
        category_breakdown = df.groupby('category')['amount'].sum().to_dict()
        
        prompt = f"""You are a financial analyst. Analyze this transaction data and provide insights.

Transaction Statistics:
- Total transactions: {total_transactions}
- Spend by currency: {spend_by_currency}
- Top merchants: {top_merchants}
- Category breakdown: {category_breakdown}
- Anomalies detected: {anomaly_count}

Generate a JSON summary with:
1. total_spend_by_currency: dict of currency to total amount
2. top_3_merchants: list of {{"merchant": name, "amount": value}} for top 3
3. anomaly_count: number of anomalies
4. narrative: 2-3 sentence business summary (spending patterns, concerns, trends)
5. risk_level: "low", "medium", or "high"

Risk level criteria:
- low: <5% anomalies, normal spending patterns
- medium: 5-15% anomalies or unusual patterns
- high: >15% anomalies or serious concerns

Return ONLY valid JSON, no additional text:
{{
  "total_spend_by_currency": {{}},
  "top_3_merchants": [],
  "anomaly_count": 0,
  "narrative": "",
  "risk_level": "low"
}}

JSON:"""
        
        return prompt
    
    def _parse_summary_response(self, response_text: str) -> Dict[str, Any]:
        """Parse summary response from Gemini."""
        try:
            # Clean response
            response_text = response_text.strip()
            
            # Remove markdown code blocks
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            summary = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['total_spend_by_currency', 'top_3_merchants', 'anomaly_count', 'narrative', 'risk_level']
            for field in required_fields:
                if field not in summary:
                    logger.warning(f"Missing field in summary: {field}, adding default")
                    summary[field] = None if field == 'narrative' else {} if 'currency' in field else [] if 'merchants' in field else 0
            
            logger.info("✓ Summary parsed successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to parse summary response: {e}")
            return {
                'total_spend_by_currency': {},
                'top_3_merchants': [],
                'anomaly_count': 0,
                'narrative': 'Summary generation failed',
                'risk_level': 'unknown'
            }
