from app.extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for
from pyotp import random_base32
from time import time
import jwt
from flask import current_app

# Define the association table for favorites
user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('agent_id', db.Integer, db.ForeignKey('agent.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    # Basic fields
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Profile fields
    avatar = db.Column(db.String(200))
    bio = db.Column(db.Text)
    website = db.Column(db.String(200))
    twitter = db.Column(db.String(200))
    github = db.Column(db.String(200))
    
    # Relationships
    owned_agents = db.relationship(
        'Agent',
        foreign_keys='Agent.user_id',
        back_populates='owner',
        lazy='dynamic'
    )
    
    submitted_agents = db.relationship(
        'Agent',
        foreign_keys='Agent.submitted_by_id',
        back_populates='submitted_by',
        lazy='dynamic'
    )
    
    reviews = db.relationship(
        'Review',
        back_populates='user',
        lazy='dynamic'
    )

    favorite_agents = db.relationship(
        'Agent',
        secondary='user_favorites',
        lazy='dynamic',
        back_populates='favorited_by'
    )

    agent_upvotes = db.relationship('AgentUpvote', 
                                  back_populates='user',
                                  cascade='all, delete-orphan')
    
    upvoted_agents = db.relationship(
        'Agent',
        secondary='agent_upvotes',
        primaryjoin="User.id==agent_upvotes.c.user_id",
        secondaryjoin="agent_upvotes.c.agent_id==Agent.id",
        back_populates='upvoted_by',
        overlaps="agent_upvotes",
        lazy='dynamic'
    )

    two_factor_secret = db.Column(db.String(32))
    two_factor_enabled = db.Column(db.Boolean, default=False)
    
    blog_posts = db.relationship('BlogPost', 
                               backref=db.backref('author', lazy=True),
                               lazy='dynamic',
                               cascade='all, delete-orphan',
                               primaryjoin="User.id == BlogPost.author_id")
    
    def get_2fa_uri(self):
        if not self.two_factor_secret:
            self.two_factor_secret = random_base32()
            db.session.commit()
        return f"otpauth://totp/Agent-Locker:{self.email}?secret={self.two_factor_secret}&issuer=Agent-Locker"

    def __init__(self, username, email, full_name=None, is_admin=False, is_verified=False, **kwargs):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.is_admin = is_admin
        self.is_verified = is_verified
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_admin': self.is_admin,
            'is_verified': self.is_verified,
            'avatar': self.avatar,
            'bio': self.bio,
            'website': self.website,
            'twitter': self.twitter,
            'github': self.github
        }

    @property
    def avatar_url(self):
        """Returns the URL for the user's avatar image"""
        if self.avatar:
            return url_for('static', filename=f'uploads/avatars/{self.avatar}')
        return None
    
    @property
    def upvoted_agent_ids(self):
        """Returns a list of agent IDs that the user has upvoted"""
        return [upvote.agent_id for upvote in self.agent_upvotes]

    def get_verification_token(self, expires_in=3600):
        return jwt.encode(
            {'verify_email': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_email_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                          algorithms=['HS256'])['verify_email']
        except:
            return None
        return User.query.get(id)