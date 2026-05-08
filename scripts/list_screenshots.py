#!/usr/bin/env python3
import os
import sys

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import create_app, db
from app.models import Agent

def list_screenshots():
    app = create_app()
    
    with app.app_context():
        # Get all agents with screenshots
        agents = Agent.query.filter(Agent.screenshot.isnot(None)).all()
        
        print(f"\nFound {len(agents)} agents with screenshots")
        
        for agent in agents:
            print(f"{agent.screenshot}")

if __name__ == "__main__":
    list_screenshots() 