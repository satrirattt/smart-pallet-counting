import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, TextIO


def summarize_csv(file_obj: TextIO) -> Dict[str, int]:
    reader = csv.DictReader(file_obj)  #อ่านไฟล์ CSV เป็นพจนานุกรม โดยแถวแรกของไฟล์ CSV จะถูกใช้เป็นหัวคอลัมน์
    required_columns = {"product_code", "quantity"}

    if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
        raise ValueError("CSV must contain product_code and quantity columns")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("CSV column names must be unique")

    totals: Dict[str, int] = defaultdict(int) #รวมจำนวนสินค้ารหัสเดียวกันด้วย defaultdict เพื่อให้ค่าเริ่มต้นเป็น 0

    for line_number, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(f"Too many values on line {line_number}")

        product_code = (row.get("product_code") or "").strip()
        if not product_code:
            raise ValueError(f"Missing product_code on line {line_number}")

        quantity_text = (row.get("quantity") or "").strip()
        try:
            quantity = int(quantity_text)
        except ValueError as error:
            raise ValueError(
                f"quantity must be an integer on line {line_number}"
            ) from error

        if quantity <= 0:
            raise ValueError(f"quantity must be greater than zero on line {line_number}")

        totals[product_code] += quantity

    return dict(totals)


def main() -> None:
    default_csv = Path(__file__).with_name("camera_counts.csv")
    parser = argparse.ArgumentParser(
        description="Summarize camera-detected quantities by product code."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        type=Path,
        default=default_csv,
        help=f"CSV input file (default: {default_csv.name})",
    )
    args = parser.parse_args()

    try:
        with args.csv_file.open(encoding="utf-8-sig", newline="") as csv_file:
            totals = summarize_csv(csv_file)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.error(str(error))

    if not totals:
        print("No count data found.")
        return

    for product_code, quantity in sorted(totals.items()):
        print(f"{product_code}: {quantity}")


if __name__ == "__main__":
    main()
