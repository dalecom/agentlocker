import sqlite3
from pathlib import Path
import os

# Get the project root directory
project_root = Path(os.getcwd())

# Set the appropriate database path
db_path = project_root / 'instance' / 'ai_directory.db'

print(f"Using database at: {db_path}")
print(f"Database exists: {db_path.exists()}")
print(f"Current working directory: {os.getcwd()}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns exist
    cursor.execute("PRAGMA table_info(agent)")
    columns = [column[1] for column in cursor.fetchall()]
    print("\nExisting columns:", columns)
    
    # Add all required sales columns if they don't exist
    required_columns = {
        'email': 'VARCHAR(255)',
        'added_on_x': 'VARCHAR(10)',
        'contacted': 'BOOLEAN NOT NULL DEFAULT 0',
        'pitched_ads': 'BOOLEAN NOT NULL DEFAULT 0',
        'sales_email_sent': 'BOOLEAN NOT NULL DEFAULT 0',
        'sales_email_sent_date': 'TIMESTAMP'
    }
    
    for col_name, col_type in required_columns.items():
        if col_name not in columns:
            print(f"Adding {col_name} column...")
            cursor.execute(f'ALTER TABLE agent ADD COLUMN {col_name} {col_type}')
    
    # Commit the changes
    conn.commit()
    print("\nColumns added successfully!")
    
    # Verify the columns were added
    cursor.execute("PRAGMA table_info(agent)")
    print("\nUpdated table schema:")
    for column in cursor.fetchall():
        print(f"- {column[1]} ({column[2]})")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    conn.rollback()

finally:
    conn.close() 