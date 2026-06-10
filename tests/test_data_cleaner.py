import unittest

from app.utils.data_cleaner import DataCleaner, clean_amount


class DataCleanerTests(unittest.TestCase):
    def test_clean_amount_preserves_decimal_and_removes_symbols(self):
        cases = {
            "$4,627.78": 4627.78,
            "₹12,500": 12500.0,
            " 9,876.50 ": 9876.50,
            "1.234,56": 1234.56,
            "USD 1,200.05": 1200.05,
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(clean_amount(raw), expected)

    def test_transaction_ids_never_expose_nan_or_duplicates(self):
        import pandas as pd

        df = pd.DataFrame({"txn_id": [None, "nan", "TXN1", "TXN1", ""]})
        cleaned = DataCleaner.normalize_transaction_ids(df)

        self.assertEqual(len(cleaned["txn_id"]), len(set(cleaned["txn_id"])))
        self.assertFalse(cleaned["txn_id"].str.lower().isin({"nan", "none", "", "undefined"}).any())
        self.assertTrue(cleaned["txn_id"].str.startswith("AUTO_TXN_").any())


if __name__ == "__main__":
    unittest.main()
