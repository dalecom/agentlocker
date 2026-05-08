#!/usr/bin/env python3
import os
import sys
import csv
from datetime import datetime

# Add the parent directory to Python path (similar to agent_scan.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import create_app, db
from app.models import Agent

def export_twitter_urls():
    app = create_app()
    
    with app.app_context():
        # Get all agents with Twitter URLs
        agents = Agent.query.filter(
            Agent.twitter_url.isnot(None),
            Agent.twitter_url != ''
        ).all()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'twitter_urls_{timestamp}.csv'
        
        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Agent Name', 'Provider', 'Twitter URL', 'Verified', 'Status'])
            
            for agent in agents:
                writer.writerow([
                    agent.name,
                    agent.provider,
                    agent.twitter_url,
                    agent.is_verified,
                    agent.status
                ])
        
        print(f"\nExport complete!")
        print(f"Total agents with Twitter URLs: {len(agents)}")
        print(f"Data exported to: {filename}")
        
        # Print sample of URLs
        print("\nSample of Twitter URLs:")
        for agent in agents[:5]:
            print(f"- {agent.name}: {agent.twitter_url}")

if __name__ == "__main__":
    export_twitter_urls()