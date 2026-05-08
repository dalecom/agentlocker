import sqlite3
import os
from pathlib import Path

# Determine if we're on PythonAnywhere
ON_PYTHONANYWHERE = 'PYTHONANYWHERE_SITE' in os.environ

# Set the appropriate database path
if ON_PYTHONANYWHERE:
    db_path = Path('/home/dcblack/ai-agent-directory/instance/ai_directory.db')
else:
    db_path = Path('instance/ai_directory.db')

def print_all_images(cursor):
    """Print all agents and their image paths"""
    # First get total count
    cursor.execute("SELECT COUNT(*) FROM agent")
    total_count = cursor.fetchone()[0]
    print(f"\nTotal agents in database: {total_count}")
    
    # Now get all agents with COALESCE to handle NULLs
    cursor.execute("""
        SELECT 
            id, 
            COALESCE(name, 'NO NAME'),
            COALESCE(logo_url, 'NO LOGO'),
            COALESCE(screenshot, 'NO SCREENSHOT')
        FROM agent 
        ORDER BY id ASC
    """)
    agents = cursor.fetchall()
    
    print(f"Fetched {len(agents)} agents")
    
    # Count file types
    png_count = 0
    webp_count = 0
    jpg_count = 0
    
    print("\nImage paths for all agents:")
    print("-" * 80)
    
    for agent_id, name, logo_url, screenshot in agents:
        print(f"\nAgent {agent_id}: {name}")
        print(f"Logo URL: {logo_url}")
        print(f"Screenshot: {screenshot}")
        
        # Count file types
        if '.png' in logo_url.lower() or '.png' in screenshot.lower():
            png_count += 1
        if '.webp' in logo_url.lower() or '.webp' in screenshot.lower():
            webp_count += 1
        if '.jpg' in logo_url.lower() or '.jpeg' in screenshot.lower():
            jpg_count += 1
            
        print("-" * 80)
    
    print("\nFile type statistics:")
    print(f"PNG files: {png_count}")
    print(f"WEBP files: {webp_count}")
    print(f"JPG files: {jpg_count}")

def main():
    print(f"Using database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First check for any NULL values
        cursor.execute("""
            SELECT COUNT(*) 
            FROM agent 
            WHERE logo_url IS NULL 
               OR screenshot IS NULL
        """)
        null_count = cursor.fetchone()[0]
        print(f"\nAgents with NULL image fields: {null_count}")
        
        print_all_images(cursor)
        
        # Double check PNG files specifically
        cursor.execute("""
            SELECT COUNT(*) 
            FROM agent 
            WHERE logo_url LIKE '%.png' 
               OR logo_url LIKE '%.PNG'
               OR screenshot LIKE '%.png'
               OR screenshot LIKE '%.PNG'
        """)
        png_files = cursor.fetchone()[0]
        print(f"\nPNG files found in database: {png_files}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        conn.close()

if __name__ == '__main__':
    main() 