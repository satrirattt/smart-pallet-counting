"""ทดสอบการรวมยอดจาก CSV และการปฏิเสธข้อมูลที่ไม่ถูกต้อง."""

import unittest
from io import StringIO
from pathlib import Path

from summarize import summarize_csv


class SummarizeCsvTests(unittest.TestCase):
    """ชุดทดสอบสำหรับฟังก์ชัน summarize_csv."""

    def test_included_camera_counts_csv(self) -> None:
        csv_file = Path(__file__).with_name("camera_counts.csv")
        with csv_file.open(encoding="utf-8-sig", newline="") as file_obj:
            totals = summarize_csv(file_obj)

        self.assertEqual(totals, {"BOX-A": 5, "BOX-B": 5, "BOX-C": 1})

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

    def test_duplicate_column_name_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "column names must be unique"):
            summarize_csv(StringIO("product_code,quantity,quantity\nBOX-A,2,3\n"))

    def test_extra_value_in_row_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Too many values on line 2"):
            summarize_csv(StringIO("product_code,quantity\nBOX-A,2,unexpected\n"))

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
