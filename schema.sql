-- ตารางเก็บผลการนับจากกล้องและข้อมูล QR ที่อ่านได้
CREATE TABLE IF NOT EXISTS camera_count_results (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL CHECK (
        timestamp = strftime('%Y-%m-%dT%H:%M:%fZ', timestamp)
    ),
    camera_id TEXT NOT NULL CHECK (
        instr(camera_id, char(0)) = 0
        AND length(trim(camera_id,
            char(9) || char(10) || char(11) || char(12) || char(13)
            || char(28, 29, 30, 31) || ' '
            || char(133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197)
            || char(8198, 8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288)
        )) > 0
    ),
    object_count INTEGER NOT NULL CHECK (
        typeof(object_count) = 'integer' AND object_count >= 0
    ),
    qr_text TEXT
);

-- รับเฉพาะ UTC แบบ ISO-8601 ที่มีความละเอียดมิลลิวินาที
DROP TRIGGER IF EXISTS trg_camera_count_valid_timestamp_insert;
DROP TRIGGER IF EXISTS trg_camera_count_valid_timestamp_update;
DROP TRIGGER IF EXISTS trg_camera_count_valid_values_insert;
DROP TRIGGER IF EXISTS trg_camera_count_valid_values_update;

CREATE TRIGGER IF NOT EXISTS trg_camera_count_valid_timestamp_insert
BEFORE INSERT ON camera_count_results
WHEN NEW.timestamp IS NULL
    OR NEW.timestamp IS NOT strftime('%Y-%m-%dT%H:%M:%fZ', NEW.timestamp)
BEGIN
    SELECT RAISE(ABORT, 'timestamp must be UTC ISO-8601 with millisecond precision');
END;

CREATE TRIGGER IF NOT EXISTS trg_camera_count_valid_timestamp_update
BEFORE UPDATE OF timestamp ON camera_count_results
WHEN NEW.timestamp IS NULL
    OR NEW.timestamp IS NOT strftime('%Y-%m-%dT%H:%M:%fZ', NEW.timestamp)
BEGIN
    SELECT RAISE(ABORT, 'timestamp must be UTC ISO-8601 with millisecond precision');
END;

CREATE TRIGGER IF NOT EXISTS trg_camera_count_valid_values_insert
BEFORE INSERT ON camera_count_results
WHEN NEW.camera_id IS NULL
    OR instr(NEW.camera_id, char(0)) > 0
    OR length(trim(NEW.camera_id,
        char(9) || char(10) || char(11) || char(12) || char(13)
        || char(28, 29, 30, 31) || ' '
        || char(133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197)
        || char(8198, 8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288)
    )) = 0
    OR typeof(NEW.object_count) <> 'integer'
    OR NEW.object_count < 0
BEGIN
    SELECT RAISE(ABORT, 'camera_id must not be blank and object_count must be a non-negative integer');
END;

CREATE TRIGGER IF NOT EXISTS trg_camera_count_valid_values_update
BEFORE UPDATE OF camera_id, object_count ON camera_count_results
WHEN NEW.camera_id IS NULL
    OR instr(NEW.camera_id, char(0)) > 0
    OR length(trim(NEW.camera_id,
        char(9) || char(10) || char(11) || char(12) || char(13)
        || char(28, 29, 30, 31) || ' '
        || char(133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197)
        || char(8198, 8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288)
    )) = 0
    OR typeof(NEW.object_count) <> 'integer'
    OR NEW.object_count < 0
BEGIN
    SELECT RAISE(ABORT, 'camera_id must not be blank and object_count must be a non-negative integer');
END;

-- เทียบเวลาแบบ UTC เพื่อรองรับข้อมูลเดิมที่เก็บ offset ต่างกัน
DROP INDEX IF EXISTS idx_camera_count_camera_timestamp;
DROP INDEX IF EXISTS idx_camera_count_camera_instant;
CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_count_camera_utc
    ON camera_count_results (
        camera_id,
        strftime('%Y-%m-%dT%H:%M:%fZ', timestamp)
    );

-- ข้อมูลจำลองสำหรับทดลองใช้งาน; แถวซ้ำจะถูกข้ามโดย unique index ด้านบน
INSERT INTO camera_count_results
    (timestamp, camera_id, object_count, qr_text)
VALUES
    ('2026-11-09T02:00:00.000Z', 'CAM-01', 3, 'PALLET-A'),
    ('2026-11-09T02:01:00.000Z', 'CAM-01', 1, NULL),
    ('2026-11-09T02:02:00.000Z', 'CAM-02', 2, 'PALLET-B'),
    ('2026-11-09T02:03:00.000Z', 'CAM-01', 0, NULL),
    ('2026-11-09T02:04:00.000Z', 'CAM-02', 4, 'PALLET-C')
ON CONFLICT DO NOTHING;
