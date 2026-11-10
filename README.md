# smart-pallet-counting (เวอร์ชันทดลอง)

ต้นแบบนับกล่องบนพาเลต ประกอบด้วยโปรแกรม Python สำหรับสรุปยอดจาก CSV และ
SQLite schema สำหรับสร้างตารางกับข้อมูลตัวอย่าง ทั้งสองส่วนยังไม่เชื่อมกัน:
โปรแกรมสรุปยอดไม่ได้บันทึกผลลงฐานข้อมูล และยังไม่มีโค้ดเชื่อมต่อกล้องหรือ YOLO

## เริ่มใช้งาน

ต้องติดตั้ง Python 3; ใช้ไลบรารีมาตรฐาน ไม่ต้องติดตั้งแพ็กเกจเพิ่ม
เปิด terminal ในโฟลเดอร์โปรเจกต์ แล้วเลือกคำสั่ง:

### สรุปยอดจาก CSV

```shell
python summarize.py
```

ใช้ `camera_counts.csv` เป็นค่าเริ่มต้น หรือระบุไฟล์อื่น:

```shell
python summarize.py path/to/camera_counts.csv
```

ผลจากไฟล์ตัวอย่าง:

```text
BOX-A: 5
BOX-B: 5
BOX-C: 1
```

### สร้างฐานข้อมูล SQLite

```shell
python init_db.py
```

คำสั่งนี้รัน `schema.sql` และสร้าง `camera_counts.db` ในโฟลเดอร์โปรเจกต์
รันซ้ำได้โดยไม่เพิ่มแถวตัวอย่างซ้ำ ไฟล์ฐานข้อมูลถูกละเว้นจาก Git

### รันทดสอบ

```shell
python -m unittest -v
```

ชุดทดสอบตรวจการสรุป CSV และพฤติกรรมของ schema โดยใช้ SQLite ชั่วคราวในหน่วยความจำ
จึงไม่เปลี่ยนไฟล์ `camera_counts.db`

## ข้อมูลที่ใช้

CSV มีคอลัมน์ `camera_id`, `captured_at`, `product_code`, `quantity` และ
`confidence`; ตัวสรุปใช้เฉพาะ `product_code` กับ `quantity` รหัสสินค้าต้องไม่ว่าง
และจำนวนต้องเป็นจำนวนเต็มบวก ส่วน `confidence` เป็นคะแนนความมั่นใจของโมเดล
ไม่ใช่การรับประกันเปอร์เซ็นต์ความถูกต้อง

ไฟล์ `schema.sql` สร้างตาราง `camera_count_results` โดยเก็บ:

| คอลัมน์ | ข้อมูล |
|---|---|
| `id` | หมายเลขรายการ สร้างโดย SQLite |
| `timestamp` | วันและเวลาที่นับ |
| `camera_id` | รหัสกล้อง |
| `object_count` | จำนวนวัตถุที่ตรวจพบ เป็นศูนย์ได้แต่ห้ามติดลบ |
| `qr_text` | ข้อความจาก QR เช่น `PALLET-A`; เป็น `NULL` เมื่อไม่มี |

## การป้องกันข้อมูลซ้ำ

Unique index บน `(camera_id, timestamp)` ห้ามกล้องเดียวกันมีรายการเวลาเดียวกันซ้ำ
และ `ON CONFLICT ... DO NOTHING` สั่งให้ SQLite ข้ามรายการซ้ำโดยไม่เขียนทับข้อมูลเดิม
กติกานี้ตรวจซ้ำจากกล้องและเวลาเท่านั้น หากตารางเดิมมีคู่ดังกล่าวซ้ำอยู่ก่อน
ต้องจัดการข้อมูลซ้ำก่อนสร้าง index

## หมายเหตุ

`schema.sql` ใช้ไวยากรณ์ SQLite ไม่ใช่ SQL Server/T-SQL หาก VS Code แจ้ง syntax
error จาก SQL Server extension ให้ตรวจ dialect ที่ extension ใช้ การตั้งค่าใน
`.vscode/settings.json` ปิดการตรวจ error ของส่วนขยายนั้นสำหรับ workspace นี้
