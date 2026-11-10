# smart-pallet-counting — Python และ SQLite Schema (เวอร์ชันทดลอง)

ชุดไฟล์ต้นแบบสำหรับทดลองสรุปผลนับกล่องบนพาเลต ประกอบด้วย:

- โปรแกรม Python สำหรับอ่าน CSV และรวมจำนวนตามรหัสสินค้า
- SQLite schema สำหรับสร้างตารางผลนับและเพิ่มข้อมูลตัวอย่าง

สองส่วนนี้ยังไม่เชื่อมกัน: Python แสดงผลรวมบนหน้าจอ แต่ไม่ได้บันทึกผลลง SQL
และโปรเจกต์ยังไม่มีโค้ดเชื่อมต่อกล้องหรือเรียกใช้ OpenCV/YOLO จริง

## เริ่มใช้งาน

ต้องติดตั้ง Python 3; โปรแกรมและชุดทดสอบใช้ไลบรารีมาตรฐานของ Python

รันตัวสรุปด้วย CSV ตัวอย่าง:

```shell
python summarize.py
```

หรือระบุไฟล์ CSV:

```shell
python summarize.py path/to/camera_counts.csv
```

ผลลัพธ์ของไฟล์ตัวอย่าง:

```text
BOX-A: 5
BOX-B: 5
BOX-C: 1
```

รันทดสอบทั้งหมด:

```shell
python -m unittest -v
```

## รูปแบบ CSV

[`camera_counts.csv`](camera_counts.csv) มีคอลัมน์ `camera_id`, `captured_at`,
`product_code`, `quantity` และ `confidence` โปรแกรมใช้เฉพาะ `product_code`
กับ `quantity` เพื่อรวมยอด คอลัมน์อื่นใช้ประกอบข้อมูลแต่ไม่มีผลต่อยอด

CSV ต้องมีคอลัมน์ `product_code` และ `quantity`; รหัสสินค้าต้องไม่ว่าง และ
จำนวนต้องเป็นจำนวนเต็มบวก แถวที่มีค่าเกินหัวตารางหรือหัวคอลัมน์ซ้ำจะถูกรายงาน
เป็นข้อผิดพลาด `confidence` เป็นคะแนนความมั่นใจจากโมเดล ไม่ใช่การรับประกัน
เปอร์เซ็นต์ความถูกต้อง

## ข้อมูลใน SQLite

[`schema.sql`](schema.sql) เป็น SQL สำหรับ SQLite สร้างตาราง
`camera_count_results` และเพิ่มข้อมูลตัวอย่าง 5 แถว แต่ละแถวเก็บข้อมูลดังนี้:

| คอลัมน์ | ข้อมูล |
|---|---|
| `id` | หมายเลขรายการ ซึ่ง SQLite กำหนดเมื่อไม่ได้ระบุ |
| `timestamp` | วันและเวลาที่นับ |
| `camera_id` | รหัสกล้อง เช่น `CAM-01` |
| `object_count` | จำนวนวัตถุที่ตรวจพบ เป็นศูนย์ได้แต่ห้ามติดลบ |
| `qr_text` | ข้อความจาก QR เช่น `PALLET-A`; เป็น `NULL` เมื่อไม่มีข้อมูล |

สร้างฐานข้อมูลแบบไฟล์ได้จากโฟลเดอร์โปรเจกต์ด้วยคำสั่งนี้:

```shell
python -c "import sqlite3; from pathlib import Path; db=sqlite3.connect('camera_counts.db'); db.executescript(Path('schema.sql').read_text(encoding='utf-8')); db.commit(); db.close()"
```

คำสั่งจะสร้าง `camera_counts.db` ในโฟลเดอร์ปัจจุบัน แล้วรัน schema เพื่อสร้าง
ตารางและเพิ่มข้อมูลตัวอย่าง ไฟล์นี้เป็นฐานข้อมูลถาวร ขณะที่ชุดทดสอบใช้ฐานข้อมูล
ในหน่วยความจำและข้อมูลจะหายเมื่อจบการทดสอบ

## ป้องกันรายการซ้ำ

schema กำหนด unique index บน `(camera_id, timestamp)` ดังนั้นกล้องตัวเดิม
จะมีรายการที่เวลาเดียวกันซ้ำไม่ได้ จากนั้น `ON CONFLICT ... DO NOTHING`
สั่งให้ SQLite ข้ามรายการซ้ำโดยไม่เพิ่มแถวและไม่เขียนทับข้อมูลเดิม

กติกานี้นิยามข้อมูลซ้ำจากรหัสกล้องและเวลาเท่านั้น ไม่ได้ป้องกันเหตุการณ์เดิม
ที่ถูกส่งมาอีกครั้งด้วย timestamp ที่ต่างกัน หากตารางเดิมมีคู่กล้อง/เวลาซ้ำ
การสร้าง unique index จะไม่สำเร็จ ต้องจัดการแถวซ้ำก่อน

## หมายเหตุ

ไฟล์ SQL ใช้ไวยากรณ์ SQLite ไม่ใช่ SQL Server/T-SQL หาก VS Code แจ้ง syntax
error จาก SQL Server extension ให้ตรวจว่า extension กำลังตรวจด้วย dialect ใด
การตั้งค่า workspace ใน [`.vscode/settings.json`](.vscode/settings.json)
ปิดการตรวจ error ของส่วนขยายนั้น เพื่อไม่ให้แจ้งเตือน T-SQL กับไฟล์ SQLite
