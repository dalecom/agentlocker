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
    # Check if slug columns exist
    cursor.execute("PRAGMA table_info(integration_method)")
    integration_columns = [column[1] for column in cursor.fetchall()]
    
    cursor.execute("PRAGMA table_info(use_case)")
    use_case_columns = [column[1] for column in cursor.fetchall()]
    
    # Handle integration_method table
    if 'slug' not in integration_columns:
        print("Adding slug column to integration_method table...")
        
        # Create new table with slug
        cursor.execute('''
            CREATE TABLE integration_method_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                slug VARCHAR(50) UNIQUE,
                description TEXT,
                icon VARCHAR(50) NOT NULL,
                color VARCHAR(7) NOT NULL,
                display_order INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        
        # Copy data
        cursor.execute('''
            INSERT INTO integration_method_new 
            SELECT id, name, NULL, description, icon, color, display_order, created_at, updated_at 
            FROM integration_method
        ''')
        
        # Drop old table
        cursor.execute('DROP TABLE integration_method')
        
        # Rename new table
        cursor.execute('ALTER TABLE integration_method_new RENAME TO integration_method')
    
    # Handle use_case table
    if 'slug' not in use_case_columns:
        print("Adding slug column to use_case table...")
        
        # Create new table with slug
        cursor.execute('''
            CREATE TABLE use_case_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                slug VARCHAR(50) UNIQUE,
                description TEXT,
                icon VARCHAR(50),
                color VARCHAR(7),
                display_order INTEGER DEFAULT 0
            )
        ''')
        
        # Copy data
        cursor.execute('''
            INSERT INTO use_case_new 
            SELECT id, name, NULL, description, icon, color, display_order 
            FROM use_case
        ''')
        
        # Drop old table
        cursor.execute('DROP TABLE use_case')
        
        # Rename new table
        cursor.execute('ALTER TABLE use_case_new RENAME TO use_case')

    # Update existing records with cleaned slugs for integration_method
    cursor.execute('''
        UPDATE integration_method 
        SET slug = LOWER(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(name, ' ', '-'),
                                    '.', '-'
                                ),
                                '/', '-'
                            ),
                            '(', ''
                        ),
                        ')', ''
                    ),
                    '&', 'and'
                ),
                "'", ''
            )
        )
    ''')
    
    # Update existing records with cleaned slugs for use_case
    cursor.execute('''
        UPDATE use_case 
        SET slug = LOWER(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        TRIM(name), ' ', '-'
                                    ),
                                    '.', '-'
                                ),
                                '/', '-'
                            ),
                            '(', ''
                        ),
                        ')', ''
                    ),
                    '&', 'and'
                ),
                "'", ''
            )
        )
    ''')
    
    # Remove any trailing hyphens
    cursor.execute('''
        UPDATE integration_method 
        SET slug = RTRIM(slug, '-')
    ''')
    
    cursor.execute('''
        UPDATE use_case 
        SET slug = RTRIM(slug, '-')
    ''')
    
    # Commit the changes
    conn.commit()
    
    # Print the updated records
    print("\nIntegration Methods:")
    cursor.execute('SELECT name, slug FROM integration_method')
    for row in cursor.fetchall():
        print(f"Name: {row[0]} -> Slug: {row[1]}")
        
    print("\nUse Cases:")
    cursor.execute('SELECT name, slug FROM use_case')
    for row in cursor.fetchall():
        print(f"Name: {row[0]} -> Slug: {row[1]}")
    
    print("\nDatabase updated successfully!")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    print(f"Current working directory: {os.getcwd()}")
    conn.rollback()

finally:
    conn.close()