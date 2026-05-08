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

def verify_and_fix_columns():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, let's backup the table
        print("Creating backup of agent table...")
        cursor.execute("CREATE TABLE IF NOT EXISTS agent_backup AS SELECT * FROM agent")
        
        # Get current columns
        cursor.execute("PRAGMA table_info(agent)")
        columns = {column[1] for column in cursor.fetchall()}
        print("\nCurrent columns:", columns)
        
        # Drop and recreate the table with all required columns
        print("\nRecreating agent table with all required columns...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_new (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            uq_agent_slug VARCHAR(100) UNIQUE,
            name VARCHAR(255),
            provider VARCHAR(255),
            description TEXT,
            short_description VARCHAR(255),
            website VARCHAR(255),
            api_endpoint VARCHAR(255),
            documentation_url VARCHAR(255),
            logo_url VARCHAR(255),
            pricing_info TEXT,
            is_verified BOOLEAN,
            verification_status VARCHAR(20),
            status VARCHAR(50),
            created_at DATETIME,
            updated_at DATETIME,
            submitted_by_id INTEGER,
            monthly_users INTEGER,
            facebook_url VARCHAR(255),
            twitter_url VARCHAR(255),
            github_url VARCHAR(255),
            discord_url VARCHAR(255),
            linkedin_url VARCHAR(255),
            screenshot VARCHAR(255),
            is_featured BOOLEAN,
            upvote_count INTEGER,
            total_reviews INTEGER,
            is_open_source BOOLEAN,
            source_repository VARCHAR(255),
            impression_count INTEGER,
            view_count INTEGER,
            click_count INTEGER,
            agent_type VARCHAR(20),
            email VARCHAR(255),
            added_on_x VARCHAR(10),
            contacted BOOLEAN,
            pitched_ads BOOLEAN,
            sales_email_sent BOOLEAN,
            sales_email_sent_date TIMESTAMP
        )
        """)
        
        # Copy data from backup to new table
        print("\nCopying data to new table...")
        cursor.execute("INSERT INTO agent_new SELECT * FROM agent_backup")
        
        # Drop old table and rename new one
        print("\nReplacing old table with new one...")
        cursor.execute("DROP TABLE agent")
        cursor.execute("ALTER TABLE agent_new RENAME TO agent")
        
        # Verify final structure
        cursor.execute("PRAGMA table_info(agent)")
        print("\nFinal table structure:")
        for column in cursor.fetchall():
            print(f"- {column[1]} ({column[2]})")
        
        # Commit changes
        conn.commit()
        print("\nDatabase update completed successfully!")
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        conn.rollback()
        print("Changes rolled back.")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_and_fix_columns() 