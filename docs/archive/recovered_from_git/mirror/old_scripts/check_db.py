import sqlite3

conn = sqlite3.connect('src/trading_data/trading.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables: {tables}")

if 'trades' in tables:
    cursor.execute("PRAGMA table_info(trades)")
    columns = cursor.fetchall()
    print(f"\\nColumns in 'trades' table:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
