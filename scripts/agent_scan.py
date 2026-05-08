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
    print("\nAgent Information:")
    print("-" * 80)
    
    all_agents = Agent.query.all()
    for agent in all_agents:
        print(f"Agent: {agent.name}")
        
        # Website URL
        if agent.website:
            print(f"Website: {agent.website}")
        
        # Documentation URL
        if agent.documentation_url:
            print(f"Documentation: {agent.documentation_url}")
        
        # Categories
        categories = [c.name for c in agent.categories]
        print(f"Categories: {', '.join(categories) if categories else 'None'}")
        
        # Use Cases
        use_cases = [uc.name for uc in agent.use_cases]
        print(f"Use Cases: {', '.join(use_cases) if use_cases else 'None'}")
        
        # Integration Methods
        integration_methods = [im.name for im in agent.integration_method_list]
        print(f"Integration Methods: {', '.join(integration_methods) if integration_methods else 'None'}")
        
        # Social Media URLs
        if agent.twitter_url:
            print(f"Twitter: {agent.twitter_url}")
        if agent.github_url:
            print(f"GitHub: {agent.github_url}")
        
        print("-" * 80)

    # Print the total count
    print(f"\nTotal Agents Found: {len(all_agents)}")