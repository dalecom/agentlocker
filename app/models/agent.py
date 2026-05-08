from app.extensions import db
from datetime import datetime
import json
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import Column, Integer, String
from json import loads, dumps
from unidecode import unidecode
import re
from .review import Review
from flask import url_for
from app.models.use_case import UseCase

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = unidecode(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

agent_use_cases = db.Table('agent_use_cases',
    db.Column('agent_id', db.Integer, db.ForeignKey('agent.id'), primary_key=True),
    db.Column('use_case_id', db.Integer, db.ForeignKey('use_case.id'), primary_key=True)
)

class AgentUpvote(db.Model):
    __tablename__ = 'agent_upvotes'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = db.relationship('Agent', 
                          back_populates='upvotes',
                          overlaps="upvoted_agents")
    user = db.relationship('User', 
                         back_populates='agent_upvotes',
                         overlaps="upvoted_agents")
    
    # Ensure a user can only upvote an agent once
    __table_args__ = (
        db.UniqueConstraint('agent_id', 'user_id', name='unique_agent_upvote'),
    )

class Agent(db.Model):
    __tablename__ = 'agent'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_agent_user_id'), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, name='uq_agent_slug')
    name = db.Column(db.String(255))
    provider = db.Column(db.String(255))
    description = db.Column(db.Text)
    short_description = db.Column(db.String(255))
    website = db.Column(db.String(255))
    api_endpoint = db.Column(db.String(255), nullable=True)
    documentation_url = db.Column(db.String(255), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    use_cases = db.relationship('UseCase', secondary=agent_use_cases,
                              lazy='subquery', backref=db.backref('agents', lazy=True))
    integration_method_list = db.relationship('IntegrationMethod', 
                                           secondary='agent_integration_methods',
                                           lazy='dynamic',
                                           back_populates='agents')
    pricing_info = db.Column(db.Text)  # Store JSON as text
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    monthly_users = db.Column(db.Integer, nullable=True)
    facebook_url = db.Column(db.String(255), nullable=True)
    twitter_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    discord_url = db.Column(db.String(255), nullable=True)  
    linkedin_url = db.Column(db.String(255), nullable=True)  
    screenshot = db.Column(db.String(255), nullable=True)  
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    upvote_count = db.Column(db.Integer, default=0)  # New column for upvotes
    is_open_source = db.Column(db.Boolean, default=False)
    source_repository = db.Column(db.String(255), nullable=True)  # For GitHub/GitLab repo URL
    impression_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    agent_type = db.Column(db.String(20), default='tool', nullable=False)  # 'tool', 'agentic', or 'platform'
    email = db.Column(db.String(255), nullable=True)
    added_on_x = db.Column(db.String(10), nullable=True)  # 'Yes', 'No', or None
    contacted = db.Column(db.Boolean, default=False)
    pitched_ads = db.Column(db.Boolean, default=False)
    sales_email_sent = db.Column(db.Boolean, default=False)
    sales_email_sent_date = db.Column(db.DateTime)

    
    favorited_by = db.relationship(
        'User',
        secondary='user_favorites',
        lazy='dynamic',
        back_populates='favorite_agents',
        primaryjoin="Agent.id==user_favorites.c.agent_id",
        secondaryjoin="user_favorites.c.user_id==User.id"
    )

    # Define relationships with explicit names and back_populates
    owner = db.relationship(
        'User',
        foreign_keys=[user_id],
        back_populates='owned_agents'
    )
    
    submitted_by = db.relationship(
        'User',
        foreign_keys=[submitted_by_id],
        back_populates='submitted_agents'
    )
    
 
    
    # Update the upvotes relationship
    upvotes = db.relationship('AgentUpvote', 
                            back_populates='agent',
                            overlaps="upvoted_agents",
                            cascade='all, delete-orphan')
    
    upvoted_by = db.relationship(
        'User',
        secondary='agent_upvotes',
        primaryjoin="Agent.id==agent_upvotes.c.agent_id",
        secondaryjoin="agent_upvotes.c.user_id==User.id",
        back_populates='upvoted_agents',
        overlaps="agent,upvotes,agent_upvotes,user",
        lazy='dynamic'
    )
    
    # Updated relationship definitions with named constraints
    categories = db.relationship('Category', 
                               secondary='agent_categories',
                               backref=db.backref('agents', lazy='dynamic'),
                               primaryjoin="Agent.id==agent_categories.c.agent_id",
                               secondaryjoin="Category.id==agent_categories.c.category_id")
    
    reviews = db.relationship('Review', 
                            back_populates='agent',
                            lazy='dynamic',
                            cascade='all, delete-orphan')
                            
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)


    @property
    def submitter(self):
        """Alias for submitted_by relationship to match template usage"""
        return self.submitted_by

    @property
    def status_display(self):
        """Get the display status of the agent"""
        if self.is_verified:
            return 'verified'
        return self.verification_status

    @property
    def screenshot_url(self):
        if self.screenshot and self.screenshot != 'None':
            return url_for('static', filename='uploads/' + self.screenshot)
        return None
    
    @property
    def logo_image_url(self):
        """Get the full URL for the agent's logo"""
        if not self.logo_url or self.logo_url == 'None':
            return url_for('static', filename='img/default-agent.png', _external=True)
        
        # If it's already a full URL, return it
        if self.logo_url.startswith(('http://', 'https://')):
            return self.logo_url
        
        # Return the direct static URL path
        return f"https://www.agentlocker.ai/static/uploads/{self.logo_url}"
    
    @property
    def pricing_model(self):
        """Get pricing model from pricing_info JSON"""
        try:
            pricing = json.loads(self.pricing_info or '{}')
            return pricing.get('model')
        except:
            return None
        
    @property
    def has_free_tier(self):
        """Get free tier status from pricing_info JSON"""
        try:
            pricing = json.loads(self.pricing_info or '{}')
            return pricing.get('free_tier', False)
        except:
            return False

    @property
    def starting_price(self):
        """Get starting price from pricing_info JSON"""
        try:
            pricing = json.loads(self.pricing_info or '{}')
            return pricing.get('starting_price')
        except:
            return None

    @property
    def price_details(self):
        """Get price details from pricing_info JSON"""
        try:
            pricing = json.loads(self.pricing_info or '{}')
            return pricing.get('price_details')
        except:
            return None

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)
    
    @average_rating.setter
    def average_rating(self, value):
        # This is a computed property, so the setter does nothing
        pass

    def generate_unique_slug(self):
        """Generate a unique URL-friendly slug from the name"""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Agent.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        self.slug = slug

    def update_rating_stats(self):
        reviews = self.reviews.all()
        if reviews:
            self.average_rating = sum(r.rating for r in reviews) / len(reviews)
            self.total_reviews = len(reviews)
        else:
            self.average_rating = 0
            self.total_reviews = 0
        
        db.session.commit()
    
    def generate_slug(self):
        """Generate a URL-friendly slug from the name"""
        self.slug = slugify(self.name)
    
    def set_capabilities(self, capabilities_list):
        if isinstance(capabilities_list, (list, tuple)):
            self.capabilities = json.dumps(list(capabilities_list))
        else:
            self.capabilities = json.dumps([])

    def get_integration_methods(self):
        """Get integration methods as a list of dictionaries"""
        try:
            if isinstance(self.integration_method_list, str):
                return json.loads(self.integration_method_list)
            return self.integration_method_list or []
        except:
            return []

    def set_integration_methods(self, methods):
        """Set integration methods from a list"""
        self.integration_method_list = json.dumps(methods)

    def set_categories(self, categories_list):
        self.categories = categories_list

    def get_capabilities(self):
        return json.loads(self.capabilities)

    def get_pricing(self):
        return json.loads(self.pricing_info)

    def set_pricing(self, pricing):
        self.pricing_info = json.dumps(pricing)

    def __repr__(self):
        return f'<Agent {self.name}>'
    
    def is_upvoted_by(self, user):
        """Check if the agent is upvoted by a specific user"""
        if not user or not user.is_authenticated:
            return False
        return self.upvoted_by.filter_by(id=user.id).first() is not None

    def toggle_upvote(self, user):
        """Toggle upvote status for a user"""
        if not user or not user.is_authenticated:
            return False
            
        if self.is_upvoted_by(user):
            self.upvoted_by.remove(user)
            self.upvote_count = max(0, self.upvote_count - 1)
            return False
        else:
            self.upvoted_by.append(user)
            self.upvote_count += 1
            return True

    def is_favorited_by(self, user):
        """Check if the agent is favorited by a specific user"""
        if not user or not user.is_authenticated:
            return False
        return self.favorited_by.filter_by(id=user.id).first() is not None

    def toggle_favorite(self, user):
        """Toggle favorite status for a user"""
        if not user or not user.is_authenticated:
            return False
            
        if self.is_favorited_by(user):
            self.favorited_by.remove(user)
            return False
        else:
            self.favorited_by.append(user)
            return True

    @property
    def twitter_handle(self):
        """Extract Twitter handle from Twitter/X URL"""
        if not self.twitter_url:
            return None
            
        # Clean and standardize the URL
        url = self.twitter_url.lower().strip()
        
        # Handle various URL formats:
        # - https://twitter.com/username
        # - twitter.com/username
        # - https://x.com/username
        # - x.com/username
        # - @username
        if url.startswith('@'):
            return url[1:]
            
        # Extract handle from URL
        match = re.search(r'(?:twitter\.com|x\.com)/([^/\?]+)', url)
        if match:
            handle = match.group(1)
            # Clean up the handle
            return handle.replace('@', '').strip()
            
        return None

class AgentCategory(db.Model):
    __tablename__ = 'agent_categories'
    agent_id = db.Column(db.Integer, 
                        db.ForeignKey('agent.id', name='fk_agent_categories_agent_id'), 
                        primary_key=True)
    category_id = db.Column(db.Integer, 
                          db.ForeignKey('category.id', name='fk_agent_categories_category_id'), 
                          primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)