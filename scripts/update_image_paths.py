#!/usr/bin/env python3
import os
import sys

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import create_app, db
from app.models import Agent

def update_image_paths():
    app = create_app()
    
    with app.app_context():
        # Get all agents with PNG or JPG files
        agents = Agent.query.filter(
            db.or_(
                Agent.logo_url.ilike('%.png'),
                Agent.logo_url.ilike('%.PNG'),
                Agent.logo_url.ilike('%.jpg'),
                Agent.logo_url.ilike('%.jpeg'),
                Agent.screenshot.ilike('%.png'),
                Agent.screenshot.ilike('%.PNG'),
                Agent.screenshot.ilike('%.jpg'),
                Agent.screenshot.ilike('%.jpeg')
            )
        ).all()
        
        print(f"\nFound {len(agents)} agents with PNG/JPG files")
        updates = 0
        
        for agent in agents:
            print(f"\nAgent {agent.id}: {agent.name}")
            print(f"Current logo: {agent.logo_url}")
            print(f"Current screenshot: {agent.screenshot}")
            
            # Handle logo_url
            if agent.logo_url and not agent.logo_url.startswith('http'):
                if agent.logo_url.lower().endswith('.png'):
                    new_logo = agent.logo_url[:-4] + '.webp'
                    agent.logo_url = new_logo
                    updates += 1
                    print(f"Updated logo: {new_logo}")
                elif agent.logo_url.lower().endswith(('.jpg', '.jpeg')):
                    new_logo = os.path.splitext(agent.logo_url)[0] + '.webp'
                    agent.logo_url = new_logo
                    updates += 1
                    print(f"Updated logo: {new_logo}")
            
            # Handle screenshot
            if agent.screenshot:
                if agent.screenshot.lower().endswith('.png'):
                    new_screenshot = agent.screenshot[:-4] + '.webp'
                    agent.screenshot = new_screenshot
                    updates += 1
                    print(f"Updated screenshot: {new_screenshot}")
                elif agent.screenshot.lower().endswith(('.jpg', '.jpeg')):
                    new_screenshot = os.path.splitext(agent.screenshot)[0] + '.webp'
                    agent.screenshot = new_screenshot
                    updates += 1
                    print(f"Updated screenshot: {new_screenshot}")
        
        # Commit all changes
        if updates > 0:
            db.session.commit()
            print(f"\nTotal updates made: {updates}")
            print("Changes committed successfully!")
        
        # Verify remaining PNG files
        remaining_png = Agent.query.filter(
            db.or_(
                Agent.logo_url.ilike('%.png'),
                Agent.logo_url.ilike('%.PNG'),
                Agent.screenshot.ilike('%.png'),
                Agent.screenshot.ilike('%.PNG')
            )
        ).count()
        
        print(f"\nPNG files remaining: {remaining_png}")

if __name__ == "__main__":
    update_image_paths()