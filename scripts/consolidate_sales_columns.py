import sqlite3
from pathlib import Path
import os

# Determine if we're on PythonAnywhere
ON_PYTHONANYWHERE = 'PYTHONANYWHERE_SITE' in os.environ

# Set the appropriate database path
if ON_PYTHONANYWHERE:
    db_path = Path('/home/dcblack/ai-agent-directory/instance/ai_directory.db')
else:
    db_path = Path('instance/ai_directory.db')

print(f"Using database at: {db_path}")
print(f"Database exists: {db_path.exists()}")
print(f"Current working directory: {os.getcwd()}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # First, let's check what columns currently exist
    cursor.execute("PRAGMA table_info(agent)")
    columns = [column[1] for column in cursor.fetchall()]
    print("\nExisting columns:", columns)
    
    # Define all the columns we need
    required_columns = {
        'email': 'VARCHAR(255)',
        'added_on_x': 'VARCHAR(10)',
        'contacted': 'BOOLEAN NOT NULL DEFAULT 0',
        'pitched_ads': 'BOOLEAN NOT NULL DEFAULT 0',
        'sales_email_sent': 'BOOLEAN NOT NULL DEFAULT 0',
        'sales_email_sent_date': 'TIMESTAMP'
    }
    
    # Add any missing columns
    for column_name, column_type in required_columns.items():
        if column_name not in columns:
            print(f"Adding {column_name} column...")
            cursor.execute(f'ALTER TABLE agent ADD COLUMN {column_name} {column_type}')
    
    # Commit the changes
    conn.commit()
    print("\nColumns added successfully!")
    
    # Verify the final schema
    cursor.execute("PRAGMA table_info(agent)")
    print("\nFinal table schema:")
    for column in cursor.fetchall():
        print(f"- {column[1]} ({column[2]})")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    conn.rollback()

finally:
    conn.close() 