import sqlite3
import shutil
import os
from pathlib import Path

storage_dir = Path("storage").resolve()
db_path = storage_dir / "app.db"

print("Starting clean of all previous video, audio, and job data...")

# 1. Clean Database
if db_path.is_file():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("Found tables in DB:", tables)
    for table in ["segments", "artifacts", "logs", "attestations", "jobs"]:
        if table in tables:
            cursor.execute(f"DELETE FROM {table};")
            print(f"Cleared table: {table}")
    conn.commit()
    conn.close()
    print("Database job records cleared successfully.")

# 2. Clean storage/jobs/
jobs_dir = storage_dir / "jobs"
if jobs_dir.is_dir():
    for item in jobs_dir.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
            print(f"Removed job directory: {item.name}")
        elif item.is_file():
            item.unlink(missing_ok=True)
            print(f"Removed job file: {item.name}")

# 3. Clean storage/uploads/
uploads_dir = storage_dir / "uploads"
if uploads_dir.is_dir():
    for item in uploads_dir.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
            print(f"Removed upload directory: {item.name}")
        elif item.is_file():
            item.unlink(missing_ok=True)
            print(f"Removed upload file: {item.name}")

# 4. Clean storage/checkpoints/ and storage/archive/
for sub in ["checkpoints", "archive"]:
    sub_dir = storage_dir / sub
    if sub_dir.is_dir():
        for item in sub_dir.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            elif item.is_file():
                item.unlink(missing_ok=True)

print("All previous video, audio, subtitle, and job data has been completely removed!")
