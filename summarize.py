import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, TextIO


def summarize_csv(file_obj: TextIO) -> Dict[str, int]:
    """รวม quantity ของแต่ละ product_code จากไฟล์ CSV."""
    reader = csv.DictReader(file_obj, strict=True)
    required_columns = {"product_code", "quantity"}

    # ตรวจหัวคอลัมน์ก่อนอ่านข้อมูล เพื่อแจ้งข้อผิดพลาดของไฟล์ได้ตรงจุด
    if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
        raise ValueError("CSV must contain product_code and quantity columns")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("CSV column names must be unique")

    # defaultdict เริ่มยอดของรหัสสินค้าใหม่ที่ 0
    totals: Dict[str, int] = defaultdict(int)

    for line_number, row in enumerate(reader, start=2):
        # DictReader เก็บข้อมูลส่วนเกินไว้ใต้ key None เมื่อแถวนั้นมีค่ามากกว่าหัวคอลัมน์
        if None in row:
            raise ValueError(f"Too many values on line {line_number}")

        product_code = (row.get("product_code") or "").strip()
        if not product_code:
            raise ValueError(f"Missing product_code on line {line_number}")

        # แปลงจำนวนเป็น integer และปฏิเสธค่าที่ไม่ใช่จำนวนเต็มบวก
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
    """อ่านไฟล์ CSV ที่ระบุและพิมพ์ยอดรวมสินค้า."""
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

    # แสดงข้อผิดพลาดผ่าน argparse แทน traceback เมื่อเปิดหรืออ่านไฟล์ไม่ได้
    try:
        with args.csv_file.open(encoding="utf-8-sig", newline="") as csv_file:
            totals = summarize_csv(csv_file)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.error(str(error))

    if not totals:
        print("No count data found.")
        return

    # เรียงรหัสสินค้าเพื่อให้ผลลัพธ์มีลำดับคงที่
    for product_code, quantity in sorted(totals.items()):
        print(f"{product_code}: {quantity}")


if __name__ == "__main__":
    main()
