from app import create_app, db
from app.models import Agent

def update_twitter_urls():
    """Update all twitter.com URLs to x.com"""
    app = create_app()
    
    with app.app_context():
        # Get all agents with Twitter URLs
        agents = Agent.query.filter(Agent.twitter_url.isnot(None)).all()
        
        updated_count = 0
        for agent in agents:
            if agent.twitter_url and 'twitter.com' in agent.twitter_url.lower():
                old_url = agent.twitter_url
                new_url = old_url.replace('twitter.com', 'x.com')
                agent.twitter_url = new_url
                updated_count += 1
                print(f"Updated {old_url} -> {new_url}")
        
        if updated_count > 0:
            db.session.commit()
            print(f"\nSuccessfully updated {updated_count} Twitter URLs to X.com")
        else:
            print("\nNo Twitter URLs needed updating")

if __name__ == '__main__':
    update_twitter_urls() 