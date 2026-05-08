import os
from pathlib import Path
from datetime import datetime
import shutil
import sqlite3

class DatabaseBackup:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define all possible database locations
        self.possible_locations = [
            Path('/home/dcblack/agentlocker/Agent-Locker/ai-agent-directory/instance/ai_directory.db'),  # First site
            Path('/home/dcblack/ai-agent-directory/instance/ai_directory.db'),  # Second site
            Path('instance/ai_directory.db'),
            Path('../instance/ai_directory.db')
        ]
        
        # Create backup directories for each site
        self.backup_dirs = {
            'site1': Path('/home/dcblack/agentlocker/Agent-Locker/ai-agent-directory/backups'),
            'site2': Path('/home/dcblack/ai-agent-directory/backups')
        }
        
        # Create backup directories if they don't exist
        for backup_dir in self.backup_dirs.values():
            backup_dir.mkdir(exist_ok=True)
            print(f"Backup directory ready: {backup_dir}")
        
        # Debug: Print current working directory
        print(f"Current directory: {Path.cwd()}")
        print("\nChecking possible database locations:")
        
        # Find all existing database files
        self.databases = []
        for loc in self.possible_locations:
            print(f"Checking: {loc}")
            if loc.exists():
                print(f"Found database! Size: {loc.stat().st_size / 1024:.2f} KB")
                self.databases.append(loc)
        
        if not self.databases:
            raise FileNotFoundError(
                "No database files found. Searched in: " + 
                ", ".join(str(p) for p in self.possible_locations)
            )
    
    def create_backup(self):
        for db_path in self.databases:
            try:
                # Determine which site this is and use appropriate backup directory
                if 'agentlocker' in str(db_path):
                    backup_dir = self.backup_dirs['site1']
                else:
                    backup_dir = self.backup_dirs['site2']
                
                # File backup
                backup_file = backup_dir / f"database_backup_{self.timestamp}_{db_path.parent.parent.name}.db"
                shutil.copy2(db_path, backup_file)
                print(f"\nCreated file backup: {backup_file}")
                
                # SQL dump backup
                dump_file = backup_dir / f"database_dump_{self.timestamp}_{db_path.parent.parent.name}.sql"
                self.create_sql_dump(db_path, dump_file)
                print(f"Created SQL dump: {dump_file}")
                
            except Exception as e:
                print(f"Error backing up {db_path}: {str(e)}")
    
    def create_sql_dump(self, source_db, dump_file):
        conn = sqlite3.connect(source_db)
        with open(dump_file, 'w') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        conn.close()

def main():
    try:
        backup = DatabaseBackup()
        backup.create_backup()
        print("\nBackup completed successfully!")
    except Exception as e:
        print(f"Error during backup: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    main()