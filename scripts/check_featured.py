#!/usr/bin/env python3
import os
import sys

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import create_app, db
from app.models import Agent

app = create_app()

with app.app_context():
    # Get all agents
    print("\nAll Agents:")
    all_agents = Agent.query.all()
    for agent in all_agents:
        print(f"- {agent.name}")
        print(f"  Featured: {agent.is_featured}")
        print(f"  Verified: {agent.is_verified}")
        print(f"  Status: {agent.status}")
        print(f"  Categories: {[c.name for c in agent.categories]}")
        print()

    # Get specifically featured agents
    print("\nFeatured Agents:")
    featured = Agent.query.filter_by(
        is_featured=True, 
        is_verified=True, 
        status='active'
    ).all()
    
    print(f"\nFound {len(featured)} featured agents:")
    for agent in featured:
        print(f"- {agent.name}")
        print(f"  Featured: {agent.is_featured}")
        print(f"  Verified: {agent.is_verified}")
        print(f"  Status: {agent.status}")
        print()

    # Print the actual SQL query
    query = Agent.query.filter_by(
        is_featured=True, 
        is_verified=True, 
        status='active'
    )
    print("\nSQL Query:")
    print(str(query))