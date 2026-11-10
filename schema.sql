-- ตารางเก็บผลการนับจากกล้องและข้อมูล QR ที่อ่านได้
CREATE TABLE IF NOT EXISTS camera_count_results (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    camera_id TEXT NOT NULL,
    object_count INTEGER NOT NULL CHECK (object_count >= 0),
    qr_text TEXT
);

-- ป้องกันการบันทึกผลซ้ำจากกล้องเดียวกันในเวลาเดียวกัน
CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_count_camera_timestamp
    ON camera_count_results (camera_id, timestamp);

-- ข้อมูลจำลองสำหรับทดลองใช้งาน; แถวซ้ำจะถูกข้ามโดย unique index ด้านบน
INSERT INTO camera_count_results
    (timestamp, camera_id, object_count, qr_text)
VALUES
    ('2026-11-09T09:00:00+07:00', 'CAM-01', 3, 'PALLET-A'),
    ('2026-11-09T09:01:00+07:00', 'CAM-01', 1, NULL),
    ('2026-11-09T09:02:00+07:00', 'CAM-02', 2, 'PALLET-B'),
    ('2026-11-09T09:03:00+07:00', 'CAM-01', 0, NULL),
    ('2026-11-09T09:04:00+07:00', 'CAM-02', 4, 'PALLET-C')
ON CONFLICT (camera_id, timestamp) DO NOTHING;
