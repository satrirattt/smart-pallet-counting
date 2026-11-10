# smart-pallet-counting

Prototype system for pallet box counting using IP camera images, OpenCV, YOLO,
QR Code detection, and a SQL database.

## CSV counting example

The CSV example treats each row as one camera detection result. Its columns are
the camera ID, capture time, product code, detected quantity, and model
confidence.

Run the example with the included five-row sample:

```shell
python summarize.py
```

Or provide another CSV file:

```shell
python summarize.py path/to/camera_counts.csv
```

The expected totals for the included sample are:

```text
BOX-A: 5
BOX-B: 5
BOX-C: 1
```

The script requires `product_code` and `quantity` columns. It reports an error
when either is missing, column names are duplicated, a row contains more values
than its header, a product code is empty, or a quantity is not a positive
integer.

## SQL example

[`schema.sql`](schema.sql) creates a SQLite table with a timestamp, camera ID,
detected object count, and optional QR text, then inserts five sample records.
`qr_text` is `NULL` when the camera does not detect a QR code. The object count
allows zero when no objects are detected. A unique index on `(camera_id,
timestamp)` identifies one event per camera at each timestamp; duplicate
inserts are ignored. Running the schema also adds the index to an existing
table. If existing rows already have duplicate camera/timestamp pairs, remove
or reconcile those duplicates before applying the schema. This assumes a camera
cannot produce two separate count events with the exact same timestamp.

## Tests

Run the CSV summarizer tests with Python's built-in test runner:

```shell
python -m unittest -v
```

The tests cover the included CSV sample, repeated product codes, an empty CSV,
missing or duplicate columns, extra row values, invalid quantities, empty
product codes, and duplicate SQL events.
