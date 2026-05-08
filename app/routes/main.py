from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from app.models.agent import Agent
from app.models.use_case import UseCase
from app.models.integration_method import IntegrationMethod
from app.models.category import Category
from sqlalchemy import func, distinct, or_, desc
from app import db
from datetime import datetime, timedelta
import markdown
from app.models.review import Review
from sqlalchemy import func
from app.models import Agent, Category, Review, User
from app.forms import ReviewForm, ContactForm  # Import your form class
from flask_mail import Mail, Message
from app import mail
from flask import current_app
from functools import wraps
import re
from flask_login import login_required, current_user
from sqlalchemy import func, distinct, or_ 
from dateutil.relativedelta import relativedelta
from app.models.agent import AgentUpvote
from app.models.blog import BlogPost, BlogCategory  # You'll need to create these models



main_bp = Blueprint('main', __name__)


def detect_bot(request):
    """Check if request is from a bot/scraper"""
    suspicious_patterns = [
        r'python-requests/',
        r'selenium',
        r'phantomjs',
        r'headless',
        r'crawler',
        r'bot'
    ]
    
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Allow legitimate Google crawlers - these are the official strings
    legitimate_crawlers = [
        'Googlebot',  # Standard Googlebot
        'Googlebot-News',
        'Googlebot-Image',
        'Googlebot-Video',
        'Googlebot-Mobile',
        'AdsBot-Google',
        'AdsBot-Google-Mobile',
        'Mediapartners-Google',  # AdSense
        'APIs-Google'
    ]
        
    if any(crawler.lower() in user_agent for crawler in legitimate_crawlers):
        return False
        
    return any(re.search(pattern, user_agent, re.I) for pattern in suspicious_patterns)



#------------------------------------------------------------------------------
# Core Page Routes
#------------------------------------------------------------------------------

@main_bp.route('/')
def index():
    """Homepage showing all agents with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    use_case_id = request.args.get('use_case', type=int)
    integration_id = request.args.get('integration', type=int)
    agent_type = request.args.get('type', 'agentic')      
    # Get latest agents
    base_query = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.agent_type == agent_type  # Add agent type filter
    )
    
    # Get categories with counts
    categories_with_counts = db.session.query(
        Category,
        func.count(distinct(Agent.id)).label('count')
    ).join(
        Agent.categories
    ).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(Category.id)\
    .order_by(Category.name)\
    .all()

    categories = []
    for category, count in categories_with_counts:
        category.agent_count = count  # Add count as attribute
        categories.append(category)
    
    # Apply category filter if specified
    if category_id:
        category = Category.query.get_or_404(category_id)
        base_query = base_query.join(Agent.categories).filter(Category.id == category_id)
    
    # Apply use case filter if specified
    if use_case_id:
        use_case = UseCase.query.get_or_404(use_case_id)
        base_query = base_query.join(Agent.use_cases).filter(UseCase.id == use_case_id)
    
    # Apply integration filter if specified
    if integration_id:
        integration = IntegrationMethod.query.get_or_404(integration_id)
        base_query = base_query.join(Agent.integration_method_list).filter(IntegrationMethod.id == integration_id)
    
    latest_agents = base_query.order_by(
        Agent.created_at.desc()
    ).paginate(
        page=1,
        per_page=18,
        error_out=False
    )
    
    # Get featured agents
    featured_agents = Agent.query.filter(
        Agent.is_featured == True,
        Agent.is_verified == True,
        Agent.status == 'active'
    ).order_by(
        func.random()
    ).limit(3).all()
    
    # Get all use cases with counts for sidebar
    use_cases_with_counts = db.session.query(
        UseCase,
        func.count(distinct(Agent.id)).label('count')
    ).join(
        Agent.use_cases
    ).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(UseCase.id)\
    .order_by(UseCase.name)\
    .all()

    use_cases = []
    for use_case, count in use_cases_with_counts:
        use_case.solution_count = count
        use_cases.append(use_case)
    
    # Get all integration methods with counts for sidebar
    integrations_with_counts = db.session.query(
        IntegrationMethod,
        func.count(distinct(Agent.id)).label('count')
    ).join(
        Agent.integration_method_list
    ).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(IntegrationMethod.id)\
    .order_by(IntegrationMethod.name)\
    .all()

    integrations = []
    for integration, count in integrations_with_counts:
        integration.agent_count = count
        integrations.append(integration)
    
    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        base_query = base_query.filter(
            or_(
                Agent.name.ilike(search_term),
                Agent.provider.ilike(search_term),
                Agent.short_description.ilike(search_term),
                Agent.description.ilike(search_term),
                Agent.categories.any(Category.name.ilike(search_term)),
                Agent.use_cases.any(UseCase.name.ilike(search_term)),
                Agent.integration_method_list.any(IntegrationMethod.name.ilike(search_term))
            )
        )
    
    # Get sort and pricing parameters
    sort = request.args.get('sort', 'newest')
    pricing = request.args.get('pricing', '')  # Add pricing parameter
    
    # Apply sorting and pricing filters
    if sort == 'newest':
        base_query = base_query.order_by(Agent.created_at.desc())
    elif sort == 'rating':
        avg_rating = db.session.query(
            Review.agent_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.agent_id).subquery()
        
        base_query = base_query.outerjoin(avg_rating, Agent.id == avg_rating.c.agent_id)\
                               .order_by(avg_rating.c.avg_rating.desc().nullslast())
    elif sort == 'reviews':
        base_query = base_query.order_by(Agent.total_reviews.desc())
    
    # Apply pricing filter
    if pricing == 'free':
        base_query = base_query.filter(
            Agent.pricing_info.isnot(None),
            Agent.pricing_info.cast(db.String).like('%"model": "free"%')
        )
    elif pricing == 'paid':
        base_query = base_query.filter(
            db.or_(
                Agent.pricing_info.is_(None),
                ~Agent.pricing_info.cast(db.String).like('%"model": "free"%')
            )
        )
    
    # Get total count before pagination
    total_agents = base_query.count()
    
    # Paginate the results
    pagination = base_query.paginate(
        page=page,
        per_page=18,
        error_out=False
    )
    
    agents = pagination.items
    
    # Keep the existing stats dictionary
    stats = {
        'total_agents': Agent.query.filter(
            Agent.is_verified == True,
            Agent.status == 'active'
        ).count(),
        'total_reviews': Review.query.count(),
        'total_categories': Category.query.count(),
        'total_use_cases': UseCase.query.count(),
        'total_integrations': IntegrationMethod.query.count()
    }
    
    # Get total counts for browse section
    total_categories = len(categories)
    total_use_cases = len(use_cases)
    total_integrations = len(integrations)
    
    # Get category stats for the count
    category_stats = Category.query.all()
    
    # Get top rated agents
    top_rated = db.session.query(
        Agent,
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('review_count')
    ).join(Review).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(Agent).having(
        func.count(Review.id) >= 1
    ).order_by(
        func.avg(Review.rating).desc()
    ).limit(10).all()
    
    # Get most reviewed agents
    most_reviewed = db.session.query(
        Agent,
        func.count(Review.id).label('review_count')
    ).join(Review).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(Agent).order_by(
        func.count(Review.id).desc()
    ).limit(7).all()

    # Get most viewed agents
    most_viewed = db.session.query(
        Agent,
        Agent.view_count.label('view_count')
    ).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).order_by(
        Agent.view_count.desc()
    ).limit(8).all()

    # Get featured agents
    featured_agents = Agent.query.filter(
        Agent.is_featured == True,
        Agent.is_verified == True,
        Agent.status == 'active'
    ).order_by(
        func.random()
    ).limit(3).all()

    return render_template('agent/list.html',
                         agents=agents,
                         categories=categories,
                         use_cases=use_cases,  # Add use cases
                         integrations=integrations,  # Add integrations
                         pagination=pagination,
                         total_agents=total_agents,
                         stats=stats,  # Add back the stats dictionary
                         total_categories=total_categories,
                         total_use_cases=total_use_cases,
                         total_integrations=total_integrations,
                         category_stats=category_stats,  # For category count
                         current_sort=sort,
                         current_search=search,
                         current_category=category_id,
                         latest_agents=latest_agents,
                         featured_agents=featured_agents,
                         agent_type=agent_type,
                         top_rated=top_rated,
                         most_reviewed=most_reviewed,
                         most_viewed=most_viewed)  # Add agent_type to template context

@main_bp.route('/about')
def about():
    """About page showing platform statistics and information."""
    
    # Get basic stats
    stats = {
        'total_agents': Agent.query.count(),
        'total_reviews': Review.query.count(),
        'total_categories': Category.query.count(),
        'total_users': User.query.count()
    }
    
    # Get monthly growth data
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    monthly_growth = [
        {
            'month': row.month,
            'count': row.count or 0
        }
        for row in db.session.query(
            func.strftime('%Y-%m', Agent.created_at).label('month'),
            func.count(Agent.id).label('count')
        ).filter(
            Agent.created_at >= twelve_months_ago
        ).group_by('month').order_by('month').all()
    ]
    
    # Get category distribution
    category_stats = [
        {
            'name': row.name,
            'count': row.agent_count
        }
        for row in db.session.query(
            Category.name,
            func.count(Agent.id).label('agent_count')
        ).join(
            Agent.categories
        ).group_by(Category.name).all()
    ]
    
    # Get integration stats
    integration_stats = [
        (method.name, len(method.agents.all()))
        for method in IntegrationMethod.query.all()
    ]
    
    # Get use case stats
    use_case_stats = [
        (use_case.name, len(use_case.agents))
        for use_case in UseCase.query.all()
    ]
    
    # Calculate average rating
    avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0
    
    # Calculate monthly growth rate
    current_month_count = Agent.query.filter(
        Agent.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    previous_month_count = Agent.query.filter(
        Agent.created_at >= datetime.utcnow() - timedelta(days=60),
        Agent.created_at < datetime.utcnow() - timedelta(days=30)
    ).count()
    
    monthly_growth_rate = 0
    if previous_month_count > 0:
        monthly_growth_rate = round(((current_month_count - previous_month_count) / previous_month_count) * 100)
    
    return render_template('main/about.html',
                         stats=stats,
                         category_stats=category_stats,
                         integration_stats=integration_stats,
                         use_case_stats=use_case_stats,
                         monthly_growth=monthly_growth,
                         avg_rating=round(avg_rating, 1),
                         monthly_growth_rate=monthly_growth_rate)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page route with form handling."""
    form = ContactForm()
    if form.validate_on_submit():
        try:
            msg = Message(
                subject=f"Contact Form: {form.subject.data}",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=['team@agentlocker.ai'],
                body=f"""
New contact form submission:

From: {form.name.data} <{form.email.data}>
Subject: {form.subject.data}

Message:
{form.message.data}
                """
            )
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            flash('An error occurred while sending your message. Please try again later.', 'error')
    
    return render_template('main/contact.html', form=form)

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page route."""
    return render_template('main/privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page route."""
    return render_template('main/terms.html')

@main_bp.route('/advertise')
def advertise():
    """Advertise page showing featured listing options."""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    # Get featured vs non-featured metrics
    featured_metrics = db.session.query(
        func.avg(Agent.impression_count).label('avg_impressions'),
        func.avg(Agent.view_count).label('avg_views'),
        func.avg(Agent.click_count).label('avg_clicks')
    ).filter(
        Agent.is_featured == True,
        Agent.is_verified == True,
        Agent.status == 'active',
    ).first()

    non_featured_metrics = db.session.query(
        func.avg(Agent.impression_count).label('avg_impressions'),
        func.avg(Agent.view_count).label('avg_views'),
        func.avg(Agent.click_count).label('avg_clicks')
    ).filter(
        Agent.is_featured == False,
        Agent.is_verified == True,
        Agent.status == 'active',
    ).first()

    # Calculate percentage differences
    comparison_stats = {
        'impressions': {
            'featured': round(featured_metrics[0] or 0, 1),
            'non_featured': round(non_featured_metrics[0] or 0, 1),
            'difference': round(((featured_metrics[0] or 0) / (non_featured_metrics[0] or 1) - 1) * 100)
        },
        'views': {
            'featured': round(featured_metrics[1] or 0, 1),
            'non_featured': round(non_featured_metrics[1] or 0, 1),
            'difference': round(((featured_metrics[1] or 0) / (non_featured_metrics[1] or 1) - 1) * 100)
        },
        'clicks': {
            'featured': round(featured_metrics[2] or 0, 1),
            'non_featured': round(non_featured_metrics[2] or 0, 1),
            'difference': round(((featured_metrics[2] or 0) / (non_featured_metrics[2] or 1) - 1) * 100)
        }
    }

    # Get other stats
    stats = {
        'total_agents': Agent.query.count(),
        'total_reviews': Review.query.count(),
        'featured_count': Agent.query.filter_by(is_featured=True).count()
    }
    
    # Get sample featured agents
    featured_examples = Agent.query\
        .filter(
            Agent.is_featured == True,
            Agent.is_verified == True,
            Agent.status == 'active'
        )\
        .order_by(func.random())\
        .limit(3)\
        .all()

    return render_template('main/advertise.html',
                         stats=stats,
                         featured_examples=featured_examples,
                         now=now,
                         timedelta=timedelta,
                         comparison_stats=comparison_stats)

#------------------------------------------------------------------------------
# Review Related Routes
#------------------------------------------------------------------------------

@main_bp.route('/reviews')
def reviews():
    """Page showing all reviews with pagination."""
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('main/reviews.html', reviews=reviews)

#------------------------------------------------------------------------------
# Category Related Routes
#------------------------------------------------------------------------------

@main_bp.route('/categories')
def categories():
    """Main categories listing page."""
    # Get categories with their agent counts
    categories_with_counts = db.session.query(
        Category,
        func.count(Agent.id).label('agent_count')
    ).join(
        Agent.categories
    ).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(Category.id)\
    .order_by(Category.name)\
    .all()

    # Convert to list of categories with count attribute
    categories = []
    for category, count in categories_with_counts:
        category.agent_count = count
        categories.append(category)

    stats = {
        'total_agents': Agent.query.count(),
        'total_reviews': Review.query.count(),
        'total_categories': len(categories)
    }
    return render_template('main/categories.html', 
                         categories=categories,
                         stats=stats)

@main_bp.route('/category/<slug>')
def category_detail(slug):
    """Generic category detail page."""
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    search = request.args.get('search', '')
    
    # Get all categories for the category switcher
    categories = Category.query.order_by(Category.name).all()
    
    # Base query for this category's agents
    base_query = Agent.query.filter(
        Agent.categories.contains(category),
        Agent.is_verified == True,
        Agent.status == 'active'
    )
    
    # Get total count before pagination
    total_agents = base_query.count()
    
    # Apply search if provided
    if search:
        base_query = base_query.filter(Agent.name.ilike(f'%{search}%'))
    
    # Apply sorting
    if sort == 'newest':
        base_query = base_query.order_by(Agent.created_at.desc())
    elif sort == 'rating':
        avg_rating = db.session.query(
            Review.agent_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.agent_id).subquery()
        
        base_query = base_query.outerjoin(avg_rating, Agent.id == avg_rating.c.agent_id)\
                               .order_by(avg_rating.c.avg_rating.desc().nullslast())
    elif sort == 'reviews':
        base_query = base_query.order_by(Agent.total_reviews.desc())
    
    # Paginate the results
    pagination = base_query.paginate(
        page=page,
        per_page=12,
        error_out=False
    )
    
    agents = pagination.items
    
    # Get related blog posts for this category
    related_posts = BlogPost.query.filter(
        BlogPost.category_id == category.id,
        BlogPost.published == True
    ).order_by(BlogPost.published_at.desc()).limit(3).all()
    
    return render_template('categories/category_detail.html',
                         category=category,
                         categories=categories,
                         agents=agents,
                         pagination=pagination,
                         total_agents=total_agents,
                         related_posts=related_posts)  # Added related_posts

#------------------------------------------------------------------------------
# Agent Related Routes
#------------------------------------------------------------------------------

@main_bp.route('/agent/<slug>')

def agent_detail(slug):
    """Individual agent detail page."""
    agent = Agent.query.filter_by(slug=slug).first_or_404()
    reviews = Review.query.filter_by(agent_id=agent.id).all()
    form = ReviewForm()

    # Get featured agents (excluding current agent)
    featured_agents = Agent.query\
        .filter(
            Agent.is_featured == True,
            Agent.is_verified == True,
            Agent.status == 'active',
            
        )\
        .order_by(func.random())\
        .limit(6)\
        .all()

    # Get similar agents based on shared categories
    similar_agents = Agent.query\
        .filter(
            Agent.categories.any(Category.id.in_([c.id for c in agent.categories])),
            Agent.id != agent.id,
            Agent.is_verified == True,
            Agent.status == 'active'
        )\
        .order_by(func.random())\
        .limit(4)\
        .all()
    
    # Debug print
    print(f"Found {len(similar_agents)} similar agents")
    for s_agent in similar_agents:
        print(f"Similar agent: {s_agent.name} (categories={[c.name for c in s_agent.categories]})")
    
    return render_template('agent/detail.html', 
                         agent=agent, 
                         reviews=reviews, 
                         featured_agents=featured_agents,
                         similar_agents=similar_agents,  # Pass similar agents to template
                         form=form)

#------------------------------------------------------------------------------
# Template Filters
#------------------------------------------------------------------------------

@main_bp.app_template_filter('markdown')
def markdown_filter(text):
    """Convert Markdown text to HTML."""
    return markdown.markdown(text)

@main_bp.app_template_filter('timeago')
def timeago(value):
    """Convert a datetime to a 'time ago' string."""
    if value is None:
        return ''
    now = datetime.utcnow()
    diff = now - value
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"

@main_bp.app_template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt is None:
        fmt = '%B %Y'
    return date.strftime(fmt)

#------------------------------------------------------------------------------
# Specific Category Routes
#------------------------------------------------------------------------------















#------------------------------------------------------------------------------
# Unsorted still
#------------------------------------------------------------------------------



@main_bp.route('/use-cases')
def use_cases():
    """Display all use cases."""
    use_cases_with_counts = db.session.query(
        UseCase,
        func.count(Agent.id).label('solution_count')
    ).join(
        Agent.use_cases
    ).group_by(UseCase.id)\
    .order_by(UseCase.name)\
    .all()

    # Convert to list of use cases with count attribute
    use_cases = []
    for use_case, count in use_cases_with_counts:
        use_case.solution_count = count
        use_cases.append(use_case)

    stats = {
        'total_agents': Agent.query.count(),
        'total_use_cases': len(use_cases)
    }
    return render_template('main/use_cases.html', 
                         use_cases=use_cases,
                         stats=stats)

@main_bp.route('/use-cases/<slug>')
def use_case_detail(slug):
    # Get the use case by slug
    use_case = UseCase.query.filter_by(slug=slug).first_or_404()
    
    # Get page number from query params
    page = request.args.get('page', 1, type=int)
    per_page = 27  # Match the number used in list_all
    sort = request.args.get('sort', 'newest')
    search = request.args.get('search', '')
    
    # Base query for agents with this use case
    base_query = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.use_cases.any(id=use_case.id)
    )
    
    # Apply search if provided
    if search:
        base_query = base_query.filter(
            or_(
                Agent.name.ilike(f'%{search}%'),
                Agent.description.ilike(f'%{search}%'),
                Agent.short_description.ilike(f'%{search}%')
            )
        )
    
    # Apply sorting
    if sort == 'rating':
        avg_rating = db.session.query(
            Review.agent_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.agent_id).subquery()
        
        base_query = base_query.outerjoin(
            avg_rating, 
            Agent.id == avg_rating.c.agent_id
        ).order_by(
            avg_rating.c.avg_rating.desc().nullslast()
        )
    elif sort == 'reviews':
        base_query = base_query.order_by(Agent.total_reviews.desc())
    else:  # newest
        base_query = base_query.order_by(Agent.created_at.desc())
    
    # Get total count before pagination
    total_agents = base_query.count()
    
    # Paginate the results
    pagination = base_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    agents = pagination.items
    
    # Get stats
    stats = {
        'total_agents': Agent.query.filter(
            Agent.is_verified == True,
            Agent.status == 'active'
        ).count(),
        'total_reviews': Review.query.count(),
        'total_categories': Category.query.count(),
        'total_use_cases': UseCase.query.count(),
        'total_integrations': IntegrationMethod.query.count()
    }
    
    # Get featured agents
    featured_agents = Agent.query.filter(
        Agent.is_featured == True,
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.use_cases.any(id=use_case.id)
    ).order_by(
        func.random()
    ).limit(3).all()
    
    return render_template('categories/use_case_detail.html',
                         use_case=use_case,
                         agents=agents,
                         pagination=pagination,
                         total_agents=total_agents,
                         stats=stats,
                         current_sort=sort,
                         current_search=search,
                         featured_agents=featured_agents)

@main_bp.route('/integrations')
def integrations():
    """Display all integrations."""
    # Get integrations with their agent counts
    integrations_with_counts = db.session.query(
        IntegrationMethod,
        func.count(Agent.id).label('agent_count')
    ).join(
        Agent.integration_method_list
    ).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(IntegrationMethod.id)\
    .order_by(IntegrationMethod.display_order)\
    .all()

    # Convert to list of integrations with count attribute
    integrations = []
    for integration, count in integrations_with_counts:
        integration.agent_count = count
        integrations.append(integration)
    
    # Get stats
    stats = {
        'total_agents': Agent.query.count(),
        'total_integrations': len(integrations)
    }
    
    return render_template('main/integrations.html', 
                         integrations=integrations,
                         stats=stats)

@main_bp.route('/integrations/<slug>')
def integration_detail(slug):
    # Get the integration method by slug
    integration_method = IntegrationMethod.query.filter_by(slug=slug).first_or_404()
    
    # Get page number from query params
    page = request.args.get('page', 1, type=int)
    per_page = 27  # Match the number used in list_all
    sort = request.args.get('sort', 'newest')
    search = request.args.get('search', '')
    
    # Base query for agents with this integration method
    base_query = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.integration_method_list.any(id=integration_method.id)
    )
    
    # Apply search if provided
    if search:
        base_query = base_query.filter(
            or_(
                Agent.name.ilike(f'%{search}%'),
                Agent.description.ilike(f'%{search}%'),
                Agent.short_description.ilike(f'%{search}%')
            )
        )
    
    # Apply sorting
    if sort == 'rating':
        avg_rating = db.session.query(
            Review.agent_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.agent_id).subquery()
        
        base_query = base_query.outerjoin(
            avg_rating, 
            Agent.id == avg_rating.c.agent_id
        ).order_by(
            avg_rating.c.avg_rating.desc().nullslast()
        )
    elif sort == 'reviews':
        base_query = base_query.order_by(Agent.total_reviews.desc())
    else:  # newest
        base_query = base_query.order_by(Agent.created_at.desc())
    
    # Get total count before pagination
    total_agents = base_query.count()
    
    # Paginate the results
    pagination = base_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    agents = pagination.items
    
    # Get stats
    stats = {
        'total_agents': Agent.query.filter(
            Agent.is_verified == True,
            Agent.status == 'active'
        ).count(),
        'total_reviews': Review.query.count(),
        'total_categories': Category.query.count(),
        'total_use_cases': UseCase.query.count(),
        'total_integrations': IntegrationMethod.query.count()
    }
    
    # Get featured agents
    featured_agents = Agent.query.filter(
        Agent.is_featured == True,
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.integration_method_list.any(id=integration_method.id)
    ).order_by(
        func.random()
    ).limit(3).all()
    
    return render_template('categories/integration_method_detail.html',
                         integration_method=integration_method,
                         agents=agents,
                         pagination=pagination,
                         total_agents=total_agents,
                         stats=stats,
                         current_sort=sort,
                         current_search=search,
                         featured_agents=featured_agents)

@main_bp.route('/stats')
def stats():
    """Statistics and analytics page showing platform metrics."""
    
    # Get basic stats
    stats = {
        'total_agents': Agent.query.filter_by(agent_type='agentic', is_verified=True, status='active').count(),
        'total_tools': Agent.query.filter_by(agent_type='tool', is_verified=True, status='active').count(),
        'total_platforms': Agent.query.filter_by(agent_type='platform', is_verified=True, status='active').count(),
        'total_categories': Category.query.count(),
        'total_use_cases': UseCase.query.count(),
        'total_integrations': IntegrationMethod.query.count()
    }
    
    # Get top 10 categories with counts and colors
    top_categories = [
        {
            'name': row.Category.name,
            'count': row.count,
            'color': row.Category.color
        }
        for row in db.session.query(
            Category,
            func.count(Agent.id).label('count')
        ).join(
            Agent.categories
        ).filter(
            Agent.is_verified == True,
            Agent.status == 'active'
        ).group_by(Category.id)\
        .order_by(func.count(Agent.id).desc())\
        .limit(10)\
        .all()
    ]
    
    # Get top 10 integrations with counts and colors
    top_integrations = [
        {
            'name': row.IntegrationMethod.name,
            'count': row.count,
            'color': row.IntegrationMethod.color
        }
        for row in db.session.query(
            IntegrationMethod,
            func.count(Agent.id).label('count')
        ).join(
            Agent.integration_method_list
        ).filter(
            Agent.is_verified == True,
            Agent.status == 'active'
        ).group_by(IntegrationMethod.id)\
        .order_by(func.count(Agent.id).desc())\
        .limit(10)\
        .all()
    ]
    
    # Get top 10 use cases with counts and colors
    top_use_cases = [
        {
            'name': row.UseCase.name,
            'count': row.count,
            'color': row.UseCase.color
        }
        for row in db.session.query(
            UseCase,
            func.count(Agent.id).label('count')
        ).join(
            Agent.use_cases
        ).filter(
            Agent.is_verified == True,
            Agent.status == 'active'
        ).group_by(UseCase.id)\
        .order_by(func.count(Agent.id).desc())\
        .limit(10)\
        .all()
    ]
    
    # Get social media platform distribution
    social_media_stats = []
    
    # Check Facebook URLs
    facebook_count = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.facebook_url.isnot(None),
        Agent.facebook_url != ''
    ).count()
    if facebook_count > 0:
        social_media_stats.append({
            'platform': 'Facebook',
            'count': facebook_count
        })
    
    # Check Twitter URLs
    twitter_count = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.twitter_url.isnot(None),
        Agent.twitter_url != ''
    ).count()
    if twitter_count > 0:
        social_media_stats.append({
            'platform': 'Twitter',
            'count': twitter_count
        })
    
    # Check GitHub URLs
    github_count = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.github_url.isnot(None),
        Agent.github_url != ''
    ).count()
    if github_count > 0:
        social_media_stats.append({
            'platform': 'GitHub',
            'count': github_count
        })
    
    # Check Discord URLs
    discord_count = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.discord_url.isnot(None),
        Agent.discord_url != ''
    ).count()
    if discord_count > 0:
        social_media_stats.append({
            'platform': 'Discord',
            'count': discord_count
        })
    
    # Check LinkedIn URLs
    linkedin_count = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active',
        Agent.linkedin_url.isnot(None),
        Agent.linkedin_url != ''
    ).count()
    if linkedin_count > 0:
        social_media_stats.append({
            'platform': 'LinkedIn',
            'count': linkedin_count
        })
    
    # Sort by count descending
    social_media_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # Get top rated agents
    top_rated = db.session.query(
        Agent,
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('review_count')
    ).join(Review).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(Agent).having(
        func.count(Review.id) >= 1
    ).order_by(
        func.avg(Review.rating).desc()
    ).limit(10).all()
    
    # Get most reviewed agents
    most_reviewed = db.session.query(
        Agent,
        func.count(Review.id).label('review_count')
    ).join(Review).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).group_by(Agent).order_by(
        func.count(Review.id).desc()
    ).limit(7).all()

    # Get most viewed agents
    most_viewed = db.session.query(
        Agent,
        Agent.view_count.label('view_count')
    ).filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    ).order_by(
        Agent.view_count.desc()
    ).limit(8).all()

    # Get featured agents
    featured_agents = Agent.query.filter(
        Agent.is_featured == True,
        Agent.is_verified == True,
        Agent.status == 'active'
    ).order_by(
        func.random()
    ).limit(3).all()

    return render_template('main/stats.html',
                         stats=stats,
                         top_categories=top_categories,
                         top_integrations=top_integrations,
                         top_use_cases=top_use_cases,
                         social_media_stats=social_media_stats,
                         featured_agents=featured_agents,
                         top_rated=top_rated,
                         most_reviewed=most_reviewed,
                         most_viewed=most_viewed)

@main_bp.route('/sitemap.xml')
def sitemap():
    """Generate sitemap with proper XML formatting"""
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/static/sitemap.xsl"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
    base_url = 'https://www.agentlocker.ai'
    
    # Add static routes
    static_routes = [
        '',  # Homepage
        '/about',
        '/contact',
        '/privacy',
        '/terms',
        '/reviews',
        '/categories',
        '/stats',
        '/integrations',
        '/use-cases',
        '/advertise',
        '/blog'  # Add blog index
    ]

    try:
        # Add all categories
        categories = Category.query.all()
        for category in categories:
            static_routes.append(f'/category/{category.slug}')

        # Add all active and verified agents
        agents = Agent.query.filter_by(status='active', is_verified=True).all()
        for agent in agents:
            static_routes.append(f'/agent/{agent.slug}')

        # Add all use cases
        use_cases = UseCase.query.all()
        for use_case in use_cases:
            static_routes.append(f'/use-cases/{use_case.slug}')

        # Add all integration methods
        integrations = IntegrationMethod.query.all()
        for integration in integrations:
            static_routes.append(f'/integrations/{integration.slug}')

        # Add all published blog posts
        blog_posts = BlogPost.query.filter_by(published=True).all()
        for post in blog_posts:
            static_routes.append(f'/blog/{post.slug}')

        # Add all blog categories
        blog_categories = BlogCategory.query.all()
        for category in blog_categories:
            static_routes.append(f'/blog/category/{category.slug}')

    except Exception as e:
        print(f"Error generating sitemap: {e}")

    # Generate XML entries with proper indentation
    for route in static_routes:
        xml_content += f'''    <url>
        <loc>{base_url}{route}</loc>
    </url>\n'''

    xml_content += '</urlset>'

    response = make_response(xml_content)
    response.headers['Content-Type'] = 'application/xml'
    response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
    
    return response


@main_bp.route('/admin/overview')
@login_required
def admin_overview():
    """Admin overview page showing platform analytics."""
    if not current_user.is_admin:
        abort(403)
        
    # Get current time and time periods
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Basic stats
    stats = {
        'total_agents': Agent.query.count(),
        'total_users': User.query.count(),
        'total_reviews': Review.query.count(),
        'total_categories': Category.query.count(),
        'total_impressions': db.session.query(func.sum(Agent.impression_count)).scalar() or 0,
        'total_views': db.session.query(func.sum(Agent.view_count)).scalar() or 0,
        'total_clicks': db.session.query(func.sum(Agent.click_count)).scalar() or 0,
        'total_upvotes': AgentUpvote.query.count(),
        'total_favorites': db.session.query(func.count()).select_from(Agent.favorited_by.property.secondary).scalar() or 0
    }

    # Generate daily stats for the last 7 days
    daily_stats = []
    for i in range(7):
        date = today - timedelta(days=i)
        next_date = date + timedelta(days=1)
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'new_agents': Agent.query.filter(
                Agent.created_at >= date,
                Agent.created_at < next_date
            ).count(),
            'new_reviews': Review.query.filter(
                Review.created_at >= date,
                Review.created_at < next_date
            ).count(),
            'new_users': User.query.filter(
                User.created_at >= date,
                User.created_at < next_date
            ).count()
        })
    daily_stats.reverse()  # Show oldest to newest

    # Generate weekly stats for the last 4 weeks
    weekly_stats = []
    for i in range(4):
        week_start = today - timedelta(days=i*7)
        week_end = week_start + timedelta(days=7)
        weekly_stats.append({
            'week': week_start.strftime('%Y-%m-%d'),
            'new_agents': Agent.query.filter(
                Agent.created_at >= week_start,
                Agent.created_at < week_end
            ).count(),
            'new_reviews': Review.query.filter(
                Review.created_at >= week_start,
                Review.created_at < week_end
            ).count(),
            'new_users': User.query.filter(
                User.created_at >= week_start,
                User.created_at < week_end
            ).count()
        })
    weekly_stats.reverse()

    # Generate monthly stats for the last 6 months
    monthly_stats = []
    for i in range(6):
        month_start = today.replace(day=1) - relativedelta(months=i)
        month_end = (month_start + relativedelta(months=1)).replace(day=1)
    monthly_stats.append({
        'month': month_start.strftime('%Y-%m'),
        'new_agents': Agent.query.filter(
            Agent.created_at >= month_start,
            Agent.created_at < month_end
        ).count(),
        'new_reviews': Review.query.filter(
            Review.created_at >= month_start,
            Review.created_at < month_end
        ).count(),
        'new_users': User.query.filter(
            User.created_at >= month_start,
            User.created_at < month_end
        ).count()
    })
    monthly_stats.reverse()

    # Generate daily metrics for the last 30 days
    daily_metrics = []
    for i in range(30):
        date = today - timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        result = db.session.query(
            func.coalesce(func.sum(Agent.impression_count), 0).label('impressions'),
            func.coalesce(func.sum(Agent.view_count), 0).label('views'),
            func.coalesce(func.sum(Agent.click_count), 0).label('clicks')
        ).filter(
            Agent.created_at < next_date
        ).first()
        
        # Convert Row to dict with explicit type conversion
        metrics_dict = {
            'date': date.strftime('%Y-%m-%d'),
            'impressions': int(result[0] or 0),
            'views': int(result[1] or 0),
            'clicks': int(result[2] or 0)
        }
        daily_metrics.insert(0, metrics_dict)
    
    # Generate weekly metrics
    weekly_metrics = []
    for i in range(12):  # Last 12 weeks
        week_start = today - timedelta(weeks=i)
        week_end = week_start + timedelta(weeks=1)
        
        result = db.session.query(
            func.coalesce(func.sum(Agent.impression_count), 0).label('impressions'),
            func.coalesce(func.sum(Agent.view_count), 0).label('views'),
            func.coalesce(func.sum(Agent.click_count), 0).label('clicks')
        ).filter(
            Agent.created_at < week_end
        ).first()
        
        # Convert Row to dict with explicit type conversion
        metrics_dict = {
            'week': week_start.strftime('%Y-%m-%d'),
            'impressions': int(result[0] or 0),
            'views': int(result[1] or 0),
            'clicks': int(result[2] or 0)
        }
        weekly_metrics.insert(0, metrics_dict)
    
    # Generate monthly metrics
    monthly_metrics = []
    for i in range(6):  # Last 6 months
        month_start = today.replace(day=1) - relativedelta(months=i)
        month_end = (month_start + relativedelta(months=1))
        
        result = db.session.query(
            func.coalesce(func.sum(Agent.impression_count), 0).label('impressions'),
            func.coalesce(func.sum(Agent.view_count), 0).label('views'),
            func.coalesce(func.sum(Agent.click_count), 0).label('clicks')
        ).filter(
            Agent.created_at < month_end
        ).first()
        
        # Convert Row to dict with explicit type conversion
        metrics_dict = {
            'month': month_start.strftime('%Y-%m'),
            'impressions': int(result[0] or 0),
            'views': int(result[1] or 0),
            'clicks': int(result[2] or 0)
        }
        monthly_metrics.insert(0, metrics_dict)

    # Get top agents by engagement
    top_agents = Agent.query\
        .order_by(Agent.view_count.desc())\
        .limit(5)\
        .all()
    
    # Get all recent activity and combine into a single sorted list
    new_agents = [{'type': 'agent', 'item': agent, 'created_at': agent.created_at} 
                  for agent in Agent.query.order_by(Agent.created_at.desc()).limit(50).all()]
    new_reviews = [{'type': 'review', 'item': review, 'created_at': review.created_at} 
                   for review in Review.query.order_by(Review.created_at.desc()).limit(50).all()]
    new_upvotes = [{'type': 'upvote', 'item': upvote, 'created_at': upvote.created_at} 
                   for upvote in AgentUpvote.query.order_by(AgentUpvote.created_at.desc()).limit(50).all()]

    # Combine all activity and sort by created_at
    recent_activity = sorted(
        new_agents + new_reviews + new_upvotes,
        key=lambda x: x['created_at'],
        reverse=True
    )[:50]  # Limit to 50 most recent items
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/overview.html',
                         stats=stats,
                         daily_stats=daily_stats,
                         weekly_stats=weekly_stats,
                         monthly_stats=monthly_stats,
                         top_agents=top_agents,
                         recent_activity=recent_activity,
                         recent_users=recent_users,
                         daily_metrics=daily_metrics,
                         weekly_metrics=weekly_metrics,
                         monthly_metrics=monthly_metrics)

@main_bp.route('/partners')
def partners():
    return render_template('main/partners.html')

#------------------------------------------------------------------------------
# Blog Related Routes
#------------------------------------------------------------------------------

@main_bp.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category')
    per_page = 10
    
    # Base query
    base_query = BlogPost.query.filter_by(published=True)
    
    # Get all categories for the category menu
    categories = BlogCategory.query.order_by(BlogCategory.name).all()
    
    # Apply category filter if specified
    if category_slug:
        category = BlogCategory.query.filter_by(slug=category_slug).first_or_404()
        base_query = base_query.filter_by(category_id=category.id)
    
    # Get total posts count for current filter
    total_posts = base_query.count()
    
    # Apply sorting and pagination
    pagination = base_query.order_by(BlogPost.published_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    posts = pagination.items
    
    return render_template('blog/index.html',
                         posts=posts,
                         categories=categories,
                         pagination=pagination,
                         total_posts=total_posts,
                         title="Blog")

@main_bp.route('/blog/<slug>')
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    
    # Get all categories for the category menu
    categories = BlogCategory.query.order_by(BlogCategory.name).all()
    
    # Get related posts from same category
    related_posts = []
    if post.category_id:
        related_posts = BlogPost.query.filter(
            BlogPost.category_id == post.category_id,
            BlogPost.id != post.id,
            BlogPost.published == True
        ).order_by(BlogPost.published_at.desc()).limit(3).all()

    featured_agents = Agent.query.filter_by(
        is_featured=True, 
        is_verified=True
    ).order_by(func.random()).limit(3)

    return render_template('blog/post.html',
                         post=post,
                         categories=categories,
                         related_posts=related_posts,
                         featured_agents=featured_agents)

@main_bp.route('/blog/category/<slug>')
def blog_category(slug):
    """Blog posts filtered by category."""
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    search = request.args.get('search', '')
    
    # Base query for posts in this category
    base_query = BlogPost.query.filter(
        BlogPost.category_id == category.id,
        BlogPost.published == True
    )
    
    # Apply search if provided
    if search:
        base_query = base_query.filter(
            or_(
                BlogPost.title.ilike(f'%{search}%'),
                BlogPost.content.ilike(f'%{search}%'),
                BlogPost.excerpt.ilike(f'%{search}%')
            )
        )
    
    # Apply sorting
    if sort == 'newest':
        base_query = base_query.order_by(BlogPost.published_at.desc())
    elif sort == 'popular':
        base_query = base_query.order_by(BlogPost.view_count.desc())
    
    # Get total count before pagination
    total_posts = base_query.count()
    
    # Paginate the results
    pagination = base_query.paginate(
        page=page,
        per_page=12,
        error_out=False
    )
    
    # Get all categories for the category switcher
    categories = BlogCategory.query.order_by(BlogCategory.name).all()
    
    # Get featured posts from this category
    featured_posts = BlogPost.query.filter(
        BlogPost.category_id == category.id,
        BlogPost.published == True,
        BlogPost.featured == True
    ).order_by(BlogPost.published_at.desc()).limit(3).all()
    
    return render_template('blog/category.html',
                         category=category,
                         categories=categories,
                         posts=pagination.items,
                         pagination=pagination,
                         total_posts=total_posts,
                         current_sort=sort,
                         current_search=search,
                         featured_posts=featured_posts)