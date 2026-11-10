# Smart Pallet Counting

ต้นแบบทดลองสรุปจำนวนสินค้าจาก CSV และสร้างฐานข้อมูลตัวอย่างด้วย Python และ SQLite
ใช้ข้อมูลจำลอง ยังไม่เชื่อมต่อกล้องหรือโมเดลตรวจจับวัตถุจริง

---

## ความสามารถ

- รวมจำนวนสินค้าตาม `product_code` จากไฟล์ CSV
- สร้างตาราง SQLite พร้อมข้อมูลตัวอย่าง
- ทดสอบการประมวลผล CSV และการป้องกันข้อมูลซ้ำ

> **ขอบเขต:** ส่วน CSV และ SQLite ยังทำงานแยกกัน ผลสรุปจาก CSV ไม่ได้บันทึก
> ลงฐานข้อมูล

---

## เริ่มใช้งาน

ต้องมี Python 3 (ทดสอบด้วย Python 3.12.10) ไม่ต้องติดตั้งแพ็กเกจเพิ่ม
เปิด Terminal ในโฟลเดอร์โปรเจกต์ แล้วเลือกรันคำสั่งที่ต้องการ:

```shell
python summarize.py
```

คำสั่งนี้อ่าน [`camera_counts.csv`](camera_counts.csv) และรวมจำนวนสินค้าตาม
`product_code` ผลลัพธ์ตัวอย่างอยู่ในหัวข้อ [ตัวอย่างผลลัพธ์](#ตัวอย่างผลลัพธ์)

สร้างฐานข้อมูลและเพิ่มข้อมูลตัวอย่างด้วย:

```shell
python init_db.py
```

คำสั่งนี้รัน [`schema.sql`](schema.sql) และสร้างไฟล์ `camera_counts.db`
พร้อมตาราง `camera_count_results` การรันซ้ำไม่เพิ่มข้อมูลตัวอย่างซ้ำ

รันชุดทดสอบด้วย:

```shell
python -m unittest -v
```

คำสั่งนี้ทดสอบการประมวลผล CSV และ schema; ผลสำเร็จจะแสดง `OK`
พร้อมจำนวน tests ที่ผ่าน

สรุปยอดจากไฟล์ CSV อื่นได้โดยระบุ path:

```shell
python summarize.py path/to/file.csv
```

CSV ต้องมีคอลัมน์ `product_code` และ `quantity`; รหัสสินค้าต้องไม่ว่าง
และจำนวนต้องเป็นจำนวนเต็มบวก

---

## ตัวอย่างผลลัพธ์

`python summarize.py` กับข้อมูลใน [`camera_counts.csv`](camera_counts.csv):

```text
BOX-A: 5
BOX-B: 5
BOX-C: 1
```

ฐานข้อมูลมีข้อมูลตัวอย่าง 5 แถว และป้องกันข้อมูลซ้ำด้วยคู่
`(camera_id, timestamp)`

ดูข้อมูลในฐานข้อมูลได้ด้วย SQLite client เช่น DB Browser for SQLite:

```sql
SELECT id, timestamp, camera_id, object_count, qr_text
FROM camera_count_results
ORDER BY timestamp;
```

---

## ข้อมูลที่จัดเก็บ

### CSV

[`camera_counts.csv`](camera_counts.csv) มีข้อมูลกล้อง เวลา รหัสสินค้า จำนวน
และ `confidence` ซึ่งเป็นคะแนนความมั่นใจ โปรแกรมสรุปใช้เฉพาะ `product_code`
กับ `quantity`; คอลัมน์อื่นเป็นข้อมูลประกอบ

### SQLite

ตาราง `camera_count_results` เก็บ:

- `id` — หมายเลขรายการ
- `timestamp` — วันที่และเวลาที่นับ
- `camera_id` — รหัสกล้อง
- `object_count` — จำนวนวัตถุ (ห้ามติดลบ; 0 ได้)
- `qr_text` — ข้อความ QR; `NULL` เมื่อไม่มี

ข้อมูล CSV และ SQLite เป็นคนละชุดตัวอย่าง จึงไม่จำเป็นต้องมีรหัสหรือยอดตรงกัน
[`schema.sql`](schema.sql) เป็นไวยากรณ์ SQLite ไม่ใช่ SQL Server/T-SQL

---

## ไฟล์ในโปรเจกต์

| ไฟล์ | หน้าที่ |
|---|---|
| [`summarize.py`](summarize.py) | ตรวจ CSV และรวมยอดสินค้าตามรหัส |
| [`camera_counts.csv`](camera_counts.csv) | ข้อมูล CSV ตัวอย่าง |
| [`init_db.py`](init_db.py) | สร้างฐานข้อมูลและเรียกใช้ schema |
| [`schema.sql`](schema.sql) | สร้างตาราง ดัชนี และข้อมูล SQLite ตัวอย่าง |
| [`test_summarize.py`](test_summarize.py) | ทดสอบการอ่านและสรุป CSV |
| [`test_schema.py`](test_schema.py) | ทดสอบตารางและการป้องกันข้อมูลซ้ำ |
| [`.gitignore`](.gitignore) | ละเว้นฐานข้อมูลและไฟล์ bytecode |
| [`.vscode/settings.json`](.vscode/settings.json) | ตั้งค่า VS Code สำหรับ SQLite schema |
