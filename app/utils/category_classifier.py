"""
Smart category classification utility.
Uses rule-based classification first, then falls back to Gemini AI for uncertain cases.
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class CategoryClassifier:
    """
    Intelligent category classifier using merchant patterns and keywords.
    Reduces reliance on AI by pre-classifying obvious merchants.
    """
    
    # Merchant pattern rules (case-insensitive)
    MERCHANT_RULES = {
        'Food': [
            r'zomato', r'swiggy', r'domino', r'pizza', r'mcdonald', r'kfc',
            r'burger', r'cafe', r'coffee', r'starbucks', r'restaurant',
            r'food', r'eatery', r'dine', r'cuisine', r'bistro', r'bakery',
            r'dunkin', r'subway', r'taco', r'wendy', r'chipotle',
            r'ubereats', r'doordash', r'grubhub', r'deliveroo'
        ],
        'Transport': [
            r'\bola\b', r'\buber\b', r'lyft', r'grab', r'taxi', r'cab',
            r'rapido', r'rideshare', r'transport', r'shuttle',
            r'metro', r'railway', r'bus', r'transit'
        ],
        'Travel': [
            r'irctc', r'makemytrip', r'goibibo', r'yatra', r'cleartrip',
            r'booking\.com', r'airbnb', r'hotel', r'airlines', r'flight',
            r'expedia', r'trivago', r'hostel', r'resort', r'travel',
            r'indigo', r'spicejet', r'airindia', r'vistara'
        ],
        'Entertainment': [
            r'netflix', r'prime\s*video', r'hotstar', r'disney', r'hulu',
            r'spotify', r'apple\s*music', r'youtube', r'bookmyshow',
            r'cinema', r'theater', r'theatre', r'movie', r'pvr', r'inox',
            r'gaming', r'xbox', r'playstation', r'steam', r'twitch'
        ],
        'Shopping': [
            r'amazon', r'flipkart', r'myntra', r'ajio', r'meesho',
            r'snapdeal', r'ebay', r'walmart', r'target', r'costco',
            r'bestbuy', r'apple\s*store', r'samsung', r'shop', r'mart',
            r'retail', r'store', r'mall', r'supermarket'
        ],
        'Utilities': [
            r'electricity', r'water', r'gas', r'utility', r'bill',
            r'internet', r'broadband', r'wifi', r'mobile\s*recharge',
            r'phone\s*bill', r'jio', r'airtel', r'vodafone', r'bsnl',
            r'power', r'energy', r'telecom'
        ],
        'Cash Withdrawal': [
            r'atm', r'cash\s*withdrawal', r'cash\s*advance', r'withdraw',
            r'atm\s*fee', r'cash\s*out'
        ]
    }
    
    # Amount-based rules (in INR)
    AMOUNT_RULES = {
        'Cash Withdrawal': lambda amt: amt >= 500 and amt % 100 == 0,  # Round amounts likely ATM
    }
    
    @classmethod
    def classify_by_rules(cls, merchant: str, amount: float, notes: Optional[str] = None) -> Optional[str]:
        """
        Classify transaction using rule-based matching.
        Returns category if confident, None if uncertain.
        """
        # Combine merchant and notes for better matching
        text = merchant.lower() if merchant else ''
        if notes and isinstance(notes, str):
            text += ' ' + notes.lower()
        
        # Check merchant patterns
        for category, patterns in cls.MERCHANT_RULES.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    logger.debug(f"Rule match: '{merchant}' -> {category} (pattern: {pattern})")
                    return category
        
        # Check amount-based rules
        for category, rule_func in cls.AMOUNT_RULES.items():
            if rule_func(amount):
                logger.debug(f"Amount rule match: {amount} -> {category}")
                return category
        
        # No confident match
        return None
    
    @classmethod
    def should_use_ai(cls, merchant: str, amount: float, notes: Optional[str] = None) -> bool:
        """
        Determine if transaction needs AI classification.
        Returns True if uncertain, False if rule-based classification is confident.
        """
        return cls.classify_by_rules(merchant, amount, notes) is None
    
    @classmethod
    def normalize_category(cls, category: str) -> str:
        """
        Normalize category names to standard format.
        Handles variations and typos.
        """
        if not category or not isinstance(category, str):
            return 'Other'
        
        category = category.strip().title()
        
        # Normalize variations
        category_map = {
            'Foods': 'Food',
            'Grocery': 'Food',
            'Groceries': 'Food',
            'Restaurant': 'Food',
            'Dining': 'Food',
            'Transportation': 'Transport',
            'Commute': 'Transport',
            'Ride': 'Transport',
            'Trip': 'Travel',
            'Vacation': 'Travel',
            'Movies': 'Entertainment',
            'Games': 'Entertainment',
            'Music': 'Entertainment',
            'E-Commerce': 'Shopping',
            'Online Shopping': 'Shopping',
            'Purchase': 'Shopping',
            'Bills': 'Utilities',
            'Recharge': 'Utilities',
            'Atm': 'Cash Withdrawal',
            'Withdrawal': 'Cash Withdrawal',
        }
        
        return category_map.get(category, category)
