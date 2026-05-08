from flask import Flask, send_from_directory, request, redirect, render_template
from flask_caching import Cache
from config import Config
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from app.extensions import db, login_manager 
from flask_mail import Mail
from app.routes.landscape import landscape_bp
from dotenv import load_dotenv
import os
from datetime import datetime
from whitenoise import WhiteNoise

load_dotenv()

# Initialize cache
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    csrf = CSRFProtect(app)

    # Configure static file handling
    app.wsgi_app = WhiteNoise(
        app.wsgi_app, 
        root='app/static/',
        prefix='static/',
        max_age=31536000  # Cache for 1 year
    )
    
    # Add MIME type handling
    app.config['MIME_TYPES'] = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
        '.ico': 'image/x-icon',
        '.svg': 'image/svg+xml',
        '.woff2': 'font/woff2',
        '.webp': 'image/webp'  
    }

    
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    
    # Add template filters
    @app.template_filter('format_number')
    def format_number(value):
        """Format numbers with K/M for thousands/millions"""
        if value is None:
            return "0"
        
        value = float(value)
        if value >= 1000000:
            return f"{value/1000000:.1f}M"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        return str(int(value))
    
    login_manager.login_view = 'auth.login'

    migrate = Migrate(app, db)

    # Import models to ensure they're registered with SQLAlchemy
    with app.app_context():
        from app.models import User, Agent, user_favorites
        from app.models.agent import Agent, AgentUpvote
        from app.models.category import Category
        from app.models.review import Review
        from app.models.use_case import UseCase

    # Import routes
    from app.routes import main, auth, agent, review, users
    from app.routes.admin import admin_bp
    
    # Register blueprints first
    app.register_blueprint(main.main_bp)
    app.register_blueprint(auth.auth_bp, url_prefix='/auth')
    app.register_blueprint(agent.agent_bp, url_prefix='/agent')
    app.register_blueprint(review.review_bp)
    app.register_blueprint(users.user_bp, url_prefix='/users')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(landscape_bp)
    
    
    @app.route('/robots.txt')
    def robots_txt():
        try:
            return send_from_directory(app.static_folder, 'robots.txt')
        except Exception as e:
            app.logger.error(f"Error serving robots.txt: {str(e)}")
            return str(e), 500

    # Add error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

@login_manager.user_loader
def load_user(id):
    from app.models.user import User
    return User.query.get(int(id))

def format_date(value, format='%B %d, %Y'):
    """Format a date using strftime."""
    if value is None:
        return ""
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return value.strftime(format)

def register_filters(app):
    """Register custom filters with the Flask app."""
    app.jinja_env.filters['date'] = format_date