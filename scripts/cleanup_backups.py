from pathlib import Path
import os
from datetime import datetime, timedelta

def cleanup_old_backups():
    # Use the same backup directories as defined in backup_db.py
    backup_dirs = {
        'site1': Path('/home/dcblack/agentlocker/Agent-Locker/ai-agent-directory/backups'),
        'site2': Path('/home/dcblack/ai-agent-directory/backups')
    }
    
    # Keep backups from last 7 days plus weekly backups for 4 weeks
    keep_daily = 7
    keep_weekly = 4
    
    for site, backup_dir in backup_dirs.items():
        if not backup_dir.exists():
            print(f"\nSkipping non-existent backup directory for {site}: {backup_dir}")
            continue
            
        print(f"\nProcessing backups for {site} in: {backup_dir}")
        
        # Get all backup files
        db_backups = sorted(backup_dir.glob('database_backup_*.db'))
        sql_backups = sorted(backup_dir.glob('database_dump_*.sql'))
        
        # Group by date
        backups_by_date = {}
        for backup in db_backups + sql_backups:
            try:
                date_str = backup.name.split('_')[2]  # Get YYYYMMDD part
                if date_str not in backups_by_date:
                    backups_by_date[date_str] = []
                backups_by_date[date_str].append(backup)
            except IndexError:
                print(f"Warning: Skipping file with unexpected name format: {backup}")
        
        # Sort dates newest to oldest
        dates = sorted(backups_by_date.keys(), reverse=True)
        
        if not dates:
            print(f"No backups found to clean up for {site}.")
            continue
        
        # Keep recent daily backups
        keep_dates = set(dates[:keep_daily])
        
        # Keep weekly backups
        for i in range(keep_weekly):
            week_idx = keep_daily + (i * 7)
            if week_idx < len(dates):
                keep_dates.add(dates[week_idx])
        
        # Delete old backups
        deleted = 0
        for date in dates:
            if date not in keep_dates:
                for backup in backups_by_date[date]:
                    try:
                        backup.unlink()
                        deleted += 1
                        print(f"Deleted old backup: {backup}")
                    except Exception as e:
                        print(f"Error deleting {backup}: {str(e)}")
        
        print(f"\nCleanup complete for {site}")
        print(f"Deleted {deleted} old backup files")
        print(f"Keeping backups from dates: {sorted(keep_dates)}")

if __name__ == "__main__":
    cleanup_old_backups()