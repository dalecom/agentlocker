import sqlite3
from pathlib import Path
import os

# Use the same path resolution as config.py
instance_dir = os.path.join(os.getcwd(), 'instance')
db_file = os.path.join(instance_dir, 'ai_directory.db')

print(f"Using database at: {db_file}")
print(f"Database exists: {os.path.exists(db_file)}")
print(f"Current working directory: {os.getcwd()}")

# List all files in instance directory
print("\nFiles in instance directory:")
for file in os.listdir(instance_dir):
    print(f"- {file}")

# Connect to the database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

try:
    # Check if the columns exist first
    cursor.execute("PRAGMA table_info(agent)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add discord_url if it doesn't exist
    if 'discord_url' not in columns:
        print("\nAdding discord_url column to agent table...")
        cursor.execute('''
        ALTER TABLE agent 
        ADD COLUMN discord_url VARCHAR(255)
        ''')
        print("Added discord_url column successfully!")
    else:
        print("\nColumn discord_url already exists in agent table")

    # Add linkedin_url if it doesn't exist
    if 'linkedin_url' not in columns:
        print("\nAdding linkedin_url column to agent table...")
        cursor.execute('''
        ALTER TABLE agent 
        ADD COLUMN linkedin_url VARCHAR(255)
        ''')
        print("Added linkedin_url column successfully!")
    else:
        print("\nColumn linkedin_url already exists in agent table")

    # Verify the columns were added
    print("\nCurrent agent table schema:")
    cursor.execute("PRAGMA table_info(agent)")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  • {column[1]} ({column[2]})")

    # Create indexes for better query performance
    print("\nCreating indexes for new columns...")
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_discord_url 
    ON agent(discord_url)
    ''')
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_linkedin_url 
    ON agent(linkedin_url)
    ''')
    print("Created indexes successfully!")

    # Show all indexes on the agent table
    print("\nCurrent indexes on agent table:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='agent'")
    indexes = cursor.fetchall()
    for index in indexes:
        print(f"  • {index[0]}")

    # Commit the changes
    conn.commit()
    print("\nAll changes committed successfully!")

    # Show some statistics
    cursor.execute("SELECT COUNT(*) FROM agent WHERE discord_url IS NOT NULL")
    discord_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM agent WHERE linkedin_url IS NOT NULL")
    linkedin_count = cursor.fetchone()[0]
    print("\nSocial media URL statistics:")
    print(f"  • Agents with Discord URLs: {discord_count}")
    print(f"  • Agents with LinkedIn URLs: {linkedin_count}")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    conn.rollback()

finally:
    conn.close()
