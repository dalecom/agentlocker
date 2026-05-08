from app import db
from datetime import datetime
from slugify import slugify
from app.models.user import User

class BlogCategory(db.Model):
    """Category model for blog posts."""
    __tablename__ = 'blog_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # FontAwesome icon class
    color = db.Column(db.String(20))  # Hex color or Tailwind class
    
    # Relationships
    posts = db.relationship('BlogPost', back_populates='category', lazy='dynamic')
    
    def __init__(self, *args, **kwargs):
        """Generate slug from name if not provided."""
        if not kwargs.get('slug') and kwargs.get('name'):
            kwargs['slug'] = slugify(kwargs.get('name'))
        super().__init__(*args, **kwargs)
    
    def __repr__(self):
        return f'<BlogCategory {self.name}>'

class BlogPost(db.Model):
    """Blog post model."""
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300))
    image_url = db.Column(db.String(500))
    published = db.Column(db.Boolean, default=False, nullable=False)
    featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    
    # Meta fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Foreign keys
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('blog_categories.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    category = db.relationship('BlogCategory', back_populates='posts')
    
    def __init__(self, *args, **kwargs):
        """Generate slug from title if not provided."""
        if not kwargs.get('slug') and kwargs.get('title'):
            kwargs['slug'] = slugify(kwargs.get('title'))
        super().__init__(*args, **kwargs)
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'
    
    @property
    def read_time(self):
        """Calculate estimated reading time in minutes."""
        words_per_minute = 200
        word_count = len(self.content.split())
        minutes = word_count / words_per_minute
        return max(1, round(minutes))
    
    def publish(self):
        """Publish the blog post."""
        self.published = True
        self.published_at = datetime.utcnow()
        db.session.commit()
    
    def unpublish(self):
        """Unpublish the blog post."""
        self.published = False
        self.published_at = None
        db.session.commit()
    
    @property
    def status(self):
        return 'Published' if self.published else 'Draft'