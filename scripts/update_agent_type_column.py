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
    # Check current agent_type column
    cursor.execute("PRAGMA table_info(agent)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'agent_type' not in columns:
        print("\nAdding agent_type column to agent table...")
        cursor.execute('''
        ALTER TABLE agent 
        ADD COLUMN agent_type VARCHAR(20) NOT NULL DEFAULT 'tool'
        ''')
        print("Added agent_type column successfully!")
    else:
        print("\nColumn agent_type already exists in agent table")
        
        # Check current values in agent_type column
        cursor.execute("SELECT DISTINCT agent_type FROM agent")
        current_types = cursor.fetchall()
        print("\nCurrent agent_type values:", [t[0] for t in current_types])

    # Verify the column and its properties
    print("\nCurrent agent table schema:")
    cursor.execute("PRAGMA table_info(agent)")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  • {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'} Default: {column[4]}")

    # Create index for better query performance
    print("\nCreating index for agent_type column...")
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_agent_type 
    ON agent(agent_type)
    ''')
    print("Created index successfully!")

    # Show all indexes on the agent table
    print("\nCurrent indexes on agent table:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='agent'")
    indexes = cursor.fetchall()
    for index in indexes:
        print(f"  • {index[0]}")

    # Show statistics for agent types
    cursor.execute("""
    SELECT agent_type, COUNT(*) as count 
    FROM agent 
    GROUP BY agent_type
    """)
    type_counts = cursor.fetchall()
    print("\nAgent type statistics:")
    for type_name, count in type_counts:
        print(f"  • {type_name}: {count} agents")

    # Commit the changes
    conn.commit()
    print("\nAll changes committed successfully!")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    conn.rollback()

finally:
    conn.close()
