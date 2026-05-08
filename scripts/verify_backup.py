import sqlite3
from pathlib import Path

def check_backup():
    # Get latest backup
    backup_dir = Path('backups')
    latest_backup = sorted(backup_dir.glob('database_backup_*.db'))[-1]
    
    print(f"Checking backup: {latest_backup}")
    
    # Connect to backup database
    conn = sqlite3.connect(latest_backup)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\nTables found:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"- {table_name}: {count} rows")
        
        # Show sample data
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
            columns = [description[0] for description in cursor.description]
            print(f"  Columns: {', '.join(columns)}\n")
    
    conn.close()

if __name__ == "__main__":
    check_backup()