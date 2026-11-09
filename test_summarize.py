import unittest
from io import StringIO

from summarize import summarize_csv


class SummarizeCsvTests(unittest.TestCase):
    def test_sums_rows_with_same_product_code(self) -> None:
        csv_data = (
            "product_code,quantity\n"
            "BOX-A,3\n"
            "BOX-A,2\n"
            "BOX-B,1\n"
        )

        self.assertEqual(
            summarize_csv(StringIO(csv_data)),
            {"BOX-A": 5, "BOX-B": 1},
        )

    def test_empty_csv_returns_empty_result(self) -> None:
        self.assertEqual(
            summarize_csv(StringIO("product_code,quantity\n")),
            {},
        )

    def test_missing_required_column_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "product_code and quantity"):
            summarize_csv(StringIO("product_code\nBOX-A\n"))

    def test_invalid_quantity_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "integer"):
            summarize_csv(StringIO("product_code,quantity\nBOX-A,abc\n"))

    def test_non_positive_quantity_raises_value_error(self) -> None:
        for quantity in ("0", "-1"):
            with self.subTest(quantity=quantity):
                with self.assertRaisesRegex(ValueError, "greater than zero"):
                    summarize_csv(
                        StringIO(f"product_code,quantity\nBOX-A,{quantity}\n")
                    )

    def test_empty_product_code_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing product_code"):
            summarize_csv(StringIO("product_code,quantity\n,2\n"))


if __name__ == "__main__":
    unittest.main()
