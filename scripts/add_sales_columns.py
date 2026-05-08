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
    # Check if columns exist
    cursor.execute("PRAGMA table_info(agent)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add email if it doesn't exist
    if 'email' not in columns:
        print("Adding email column...")
        cursor.execute('ALTER TABLE agent ADD COLUMN email VARCHAR(255)')
    
    # Add added_on_x if it doesn't exist
    if 'added_on_x' not in columns:
        print("Adding added_on_x column...")
        cursor.execute('ALTER TABLE agent ADD COLUMN added_on_x VARCHAR(10)')
    
    # Add contacted if it doesn't exist
    if 'contacted' not in columns:
        print("Adding contacted column...")
        cursor.execute('ALTER TABLE agent ADD COLUMN contacted BOOLEAN NOT NULL DEFAULT 0')
    
    # Add pitched_ads if it doesn't exist
    if 'pitched_ads' not in columns:
        print("Adding pitched_ads column...")
        cursor.execute('ALTER TABLE agent ADD COLUMN pitched_ads BOOLEAN NOT NULL DEFAULT 0')
    
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