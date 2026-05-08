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
    # Create blog_categories table first (since blog_posts references it)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blog_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(200) NOT NULL,
        slug VARCHAR(200) NOT NULL UNIQUE,
        description TEXT,
        icon VARCHAR(200),
        color VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("\nCreated blog_categories table")

    # Create blog_posts table with updated schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blog_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200) NOT NULL,
        slug VARCHAR(200) NOT NULL UNIQUE,
        content TEXT NOT NULL,
        excerpt VARCHAR(500),
        image_url VARCHAR(500),
        published BOOLEAN DEFAULT 0,
        featured BOOLEAN DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        published_at TIMESTAMP,
        author_id INTEGER,
        category_id INTEGER,
        FOREIGN KEY (author_id) REFERENCES user(id),
        FOREIGN KEY (category_id) REFERENCES blog_categories(id)
    )
    ''')
    print("\nCreated blog_posts table")

    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_author ON blog_posts(author_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_category ON blog_posts(category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(published)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_featured ON blog_posts(featured)')
    print("Created indexes")

    # Verify the tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_posts'")
    tables = cursor.fetchall()
    print("\nCreated tables:")
    for table in tables:
        print(f"- {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  • {column[1]} ({column[2]})")

    # Commit the changes
    conn.commit()
    print("\nAll changes committed successfully!")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    conn.rollback()

finally:
    conn.close()