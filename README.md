# Smart Pallet Counting

ระบบตัวอย่างสำหรับสรุปจำนวนสินค้าจาก CSV และสร้างฐานข้อมูลด้วย Python และ SQLite
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
หาก schema มีข้อผิดพลาด การเปลี่ยนแปลงรอบนั้นจะถูก rollback; ถ้าฐานข้อมูลเดิม
มีข้อมูลผิดรูปแบบหรือแถวซ้ำ โปรแกรมจะแจ้ง `id` ให้แก้ก่อน โดยไม่ลบข้อมูลเดิม

รันชุดทดสอบด้วย:

```shell
python -m unittest -v
```

คำสั่งนี้ทดสอบการประมวลผล CSV และ schema; ผลสำเร็จจะแสดง `OK`
พร้อมจำนวน tests ที่ผ่าน

### Test cases ที่ครอบคลุม (15 รายการ)

- **CSV (9 รายการ):** ตรวจการสรุปยอด และปฏิเสธไฟล์หรือข้อมูลที่ไม่ถูกต้อง
- **SQLite (6 รายการ):** ตรวจ schema, การป้องกันข้อมูลซ้ำ, การปฏิเสธข้อมูลผิดรูปแบบ และ rollback

**ตัวอย่าง test case:**

| ส่วน | ข้อมูลทดสอบ | ผลที่คาดหวัง |
|---|---|---|
| CSV | `BOX-A` จำนวน 3 และ 2 ในคนละแถว | สรุปได้ `BOX-A: 5` |
| CSV | `quantity` เป็น `0` | แจ้งข้อผิดพลาด |
| SQLite | เพิ่มข้อมูลด้วย `camera_id` และเวลาเดิมซ้ำ | ไม่เพิ่มแถวใหม่ |

รายละเอียดอยู่ใน [`test_summarize.py`](test_summarize.py) และ
[`test_schema.py`](test_schema.py) การรันทดสอบยืนยันพฤติกรรมของโค้ดกับข้อมูลจำลอง
ไม่ได้ทดสอบการเชื่อมต่อหรือการตรวจจับจากกล้องจริง

สรุปยอดจากไฟล์ CSV อื่นได้โดยระบุ path:

```shell
python summarize.py path/to/file.csv
```

CSV ต้องมีคอลัมน์ `product_code` และ `quantity`; รหัสสินค้าต้องไม่ว่าง
และจำนวนต้องเป็นจำนวนเต็มบวก รูปแบบ CSV ที่มีเครื่องหมาย quote ผิดก็จะถูกปฏิเสธ

---

## ตัวอย่างผลลัพธ์

`python summarize.py` กับข้อมูลใน [`camera_counts.csv`](camera_counts.csv):

```text
BOX-A: 5
BOX-B: 5
BOX-C: 1
```

ฐานข้อมูลมีข้อมูลตัวอย่าง 5 แถว และป้องกันข้อมูลซ้ำด้วยคู่
`(camera_id, timestamp)` โดยจัดเก็บเวลาใหม่เป็น UTC รูปแบบ
`YYYY-MM-DDTHH:MM:SS.mmmZ` (ความละเอียดมิลลิวินาที) เวลาอื่นต้องแปลงเป็น UTC
ก่อนบันทึก; ข้อมูลเดิมที่ใช้ timezone offset ยังเทียบซ้ำกับเวลา UTC ได้
`camera_id` ต้องไม่ว่าง และ `object_count` ต้องเป็นจำนวนเต็มตั้งแต่ 0 ขึ้นไป

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

ไฟล์ CSV อย่างน้อยต้องมีสองคอลัมน์นี้:

```csv
product_code,quantity
BOX-A,3
BOX-A,2
BOX-B,1
```

เมื่อรัน `python summarize.py` จะรวมแถว `BOX-A` เป็น 5 และแสดง:

```text
BOX-A: 5
BOX-B: 1
```

### SQLite

ตาราง `camera_count_results` เก็บ:

- `id` — หมายเลขรายการ
- `timestamp` — วันที่และเวลาที่นับ
- `camera_id` — รหัสกล้อง
- `object_count` — จำนวนวัตถุ (ห้ามติดลบ; 0 ได้)
- `qr_text` — ข้อความ QR; `NULL` เมื่อไม่มี

ตารางนี้ไม่มีคอลัมน์ `product_code`; รหัส `BOX-A`/`BOX-B` อยู่ใน CSV เท่านั้น
และ `qr_text` เป็นข้อความ QR ไม่ใช่รหัสสินค้า ข้อมูล CSV กับ SQLite ยังไม่เชื่อมกัน
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
