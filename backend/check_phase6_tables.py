import sqlite3

conn = sqlite3.connect('docforge.db')
cursor = conn.cursor()

# Check for Phase 6 tables
phase6_tables = ['review_sessions', 'review_findings', 'edit_proposals']
print("Checking Phase 6 tables:")
for table in phase6_tables:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
    result = cursor.fetchone()
    if result:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  ✅ {table} (exists, {count} rows)")
    else:
        print(f"  ❌ {table} (NOT FOUND)")

conn.close()
