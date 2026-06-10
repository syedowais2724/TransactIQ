"""
Anomaly detection utilities for transaction data.
Flags suspicious transactions based on amount and currency patterns.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in transaction data."""
    
    # Indian merchants that should use INR
    INDIAN_MERCHANTS = ['SWIGGY', 'OLA', 'IRCTC']
    
    @staticmethod
    def detect_amount_anomalies(df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag transactions with amount > 3x account median.
        Calculates median per account_id and marks anomalies.
        """
        # Calculate median amount per account
        account_medians = df.groupby('account_id')['amount'].transform('median')
        
        # Flag anomalies where amount > 3x median
        df['is_anomaly'] = df['amount'] > (3 * account_medians)
        df['anomaly_reason'] = df.apply(
            lambda row: f"Amount {row['amount']} exceeds 3x account median ({account_medians[row.name]:.2f})"
            if row['is_anomaly'] else None,
            axis=1
        )
        
        anomaly_count = df['is_anomaly'].sum()
        logger.info(f"Detected {anomaly_count} amount-based anomalies")
        
        return df
    
    @classmethod
    def detect_currency_anomalies(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag USD transactions for Indian merchants.
        Indian merchants (Swiggy, Ola, IRCTC) should use INR.
        """
        # Normalize merchant names for comparison
        df['merchant_upper'] = df['merchant'].str.upper().str.strip()
        
        # Detect currency mismatches
        currency_mismatch = (
            df['merchant_upper'].str.contains('|'.join(cls.INDIAN_MERCHANTS), regex=True, na=False) &
            (df['currency'] == 'USD')
        )
        
        already_flagged = currency_mismatch & df['is_anomaly']
        newly_flagged = currency_mismatch & ~df['is_anomaly']

        df.loc[newly_flagged, 'is_anomaly'] = True
        df.loc[newly_flagged, 'anomaly_reason'] = "USD currency used with Indian merchant"
        df.loc[already_flagged & df['anomaly_reason'].notna(), 'anomaly_reason'] += " | USD currency used with Indian merchant"
        df.loc[already_flagged & df['anomaly_reason'].isna(), 'anomaly_reason'] = "USD currency used with Indian merchant"
        
        # Drop temporary column
        df = df.drop(columns=['merchant_upper'])
        
        currency_anomaly_count = currency_mismatch.sum()
        logger.info(f"Detected {currency_anomaly_count} currency-based anomalies")
        
        return df
    
    @classmethod
    def detect_all_anomalies(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all anomaly detection methods.
        Returns DataFrame with is_anomaly and anomaly_reason columns populated.
        """
        # Initialize anomaly columns
        df['is_anomaly'] = False
        df['anomaly_reason'] = None
        
        # Run detection methods
        df = cls.detect_amount_anomalies(df)
        df = cls.detect_currency_anomalies(df)
        
        total_anomalies = df['is_anomaly'].sum()
        logger.info(f"Total anomalies detected: {total_anomalies}")
        
        return df
