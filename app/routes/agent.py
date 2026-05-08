from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db, cache
from app.models.agent import Agent, AgentCategory
from app.models.category import Category
from app.utils.helpers import save_image, generate_slug, send_listing_approved_email, send_admin_listing_notification
from app.forms import AgentForm
from sqlalchemy import or_, desc, func, distinct
from app.models.review import Review
from flask_wtf import FlaskForm
import json
from app.models import Agent, Review, AgentCategory
from app.forms import ReviewForm
from app.forms import AgentForm, ReviewForm  
from app.models.agent import Agent, AgentCategory, AgentUpvote  
from datetime import datetime
from app.models.use_case import UseCase
from app.models.integration_method import IntegrationMethod
from app.models.user import User
from flask import render_template, request, current_app
from app.models import Agent, Category, Review, User
from app import db
from sqlalchemy import func


agent_bp = Blueprint('agent', __name__)

class ReviewForm(FlaskForm):
    pass  # We only need this for CSRF protection


@agent_bp.route('/<int:agent_id>/submit_review', methods=['POST'])
@login_required
def submit_review(agent_id):
    try:
        data = request.get_json()
        rating = int(data.get('rating'))
        content = data.get('review_text')  # Get as review_text from form
        
        if not rating or not content:
            return jsonify({'success': False, 'message': 'Rating and review content are required'}), 400
            
        # Check if user has already reviewed this agent
        existing_review = Review.query.filter_by(
            agent_id=agent_id,
            user_id=current_user.id
        ).first()
        
        if existing_review:
            return jsonify({'success': False, 'message': 'You have already reviewed this agent'}), 400
            
        # Create new review using the correct field name (content)
        review = Review(
            agent_id=agent_id,
            user_id=current_user.id,
            rating=rating,
            content=content,  # Changed to match the model
            title="Review"  # Optional: Add a default title or get from form
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting review: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@agent_bp.route('/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit(slug):
    agent = Agent.query.filter_by(slug=slug).first_or_404()
    form = AgentForm()
    
    print(f"Request method: {request.method}")  # Debug log
    print(f"Form data: {request.form}")  # Debug form data
    
    if request.method == 'POST':
        print("POST request received")
        print("CSRF Token:", form.csrf_token.data)
        if not form.validate():
            print("Form validation failed")
            print("Form errors:", form.errors)
        else:
            print("Form validation successful")
    
    # Get all categories and use cases with their metadata
    categories = Category.query.order_by(Category.display_order).all()  
    use_cases = UseCase.query.order_by(UseCase.display_order).all()
    integration_methods = IntegrationMethod.query.order_by(IntegrationMethod.display_order).all()
    
    # Populate choices
    form.categories.choices = [(str(c.id), c.name) for c in categories]
    form.use_cases.choices = [(str(u.id), u.name) for u in use_cases]
    form.integration_methods.choices = [(str(m.id), m.name) for m in integration_methods]
    
    print(f"Form submitted: {form.is_submitted()}")  # Debug log
    print(f"Form validated: {form.validate()}")  # Debug log
    
    if form.validate_on_submit():
        print("Form validation successful")  # Debug log
        try:
            # Update agent with form data
            old_name = agent.name
            agent.name = form.name.data
            
            # Update slug if name has changed
            if old_name != form.name.data:
                agent.slug = generate_slug(form.name.data)
            
            agent.provider = form.provider.data
            agent.description = form.description.data
            agent.short_description = form.short_description.data
            agent.website = form.website.data
            agent.api_endpoint = form.api_endpoint.data
            agent.documentation_url = form.documentation_url.data if form.documentation_url.data else None
            agent.facebook_url = form.facebook_url.data
            agent.twitter_url = form.twitter_url.data
            agent.github_url = form.github_url.data
            agent.discord_url = form.discord_url.data
            agent.linkedin_url = form.linkedin_url.data
            agent.monthly_users = form.monthly_users.data
            agent.is_open_source = form.is_open_source.data
            if agent.is_open_source and form.source_repository.data and form.source_repository.data.strip():
                agent.source_repository = form.source_repository.data.strip()
            else:
                agent.source_repository = None
            agent.agent_type = form.agent_type.data

            # Handle use cases
            if form.use_cases.data:
                selected_use_case_ids = [int(uc_id) for uc_id in form.use_cases.data]
                selected_use_cases = UseCase.query.filter(UseCase.id.in_(selected_use_case_ids)).all()
                agent.use_cases = selected_use_cases

            # Handle integration methods
            if form.integration_methods.data:
                selected_method_ids = [int(m_id) for m_id in form.integration_methods.data]
                selected_methods = IntegrationMethod.query.filter(IntegrationMethod.id.in_(selected_method_ids)).all()
                agent.integration_method_list = selected_methods

            # Handle categories
            if form.categories.data:
                selected_category_ids = [int(cat_id) for cat_id in form.categories.data]
                selected_categories = Category.query.filter(Category.id.in_(selected_category_ids)).all()
                agent.categories = selected_categories

            # Update pricing information
            pricing_info = {
                "model": form.pricing_model.data,
                "free_tier": form.has_free_tier.data,
                "starting_price": form.starting_price.data,
                "price_details": form.price_details.data,
            }
            agent.pricing_info = json.dumps(pricing_info)

            # Handle logo upload
            if form.logo.data:
                logo_url = save_image(form.logo.data)
                agent.logo_url = logo_url

            # Handle screenshot upload
            if form.screenshot.data:
                screenshot_path = save_image(form.screenshot.data)
                agent.screenshot = screenshot_path.split('/')[-1]

            db.session.commit()
            flash('Agent updated successfully!', 'success')
            return redirect(url_for('agent.detail', slug=agent.slug))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating agent: {str(e)}', 'error')
            print(f"Error updating agent: {str(e)}")
    
    # If GET request or form validation failed, populate form with existing data
    if request.method == 'GET':
        form.name.data = agent.name
        form.provider.data = agent.provider
        form.description.data = agent.description
        form.short_description.data = agent.short_description
        form.website.data = agent.website
        form.api_endpoint.data = agent.api_endpoint
        form.documentation_url.data = agent.documentation_url if agent.documentation_url not in [None, 'None'] else ''
        form.facebook_url.data = agent.facebook_url
        form.twitter_url.data = agent.twitter_url
        form.github_url.data = agent.github_url
        form.discord_url.data = agent.discord_url
        form.linkedin_url.data = agent.linkedin_url
        form.use_cases.data = [str(uc.id) for uc in agent.use_cases]
        form.categories.data = [str(c.id) for c in agent.categories]
        form.integration_methods.data = [str(m.id) for m in agent.integration_method_list]
        form.is_open_source.data = agent.is_open_source
        form.source_repository.data = agent.source_repository if agent.source_repository not in [None, 'None'] else ''
        form.agent_type.data = agent.agent_type
        
        # Load pricing info
        if agent.pricing_info:
            pricing = json.loads(agent.pricing_info)
            form.pricing_model.data = pricing.get('model')
            form.has_free_tier.data = pricing.get('free_tier')
            form.starting_price.data = pricing.get('starting_price')
            form.price_details.data = pricing.get('price_details')
    
    if form.errors:
        print("Form validation errors:", form.errors)
        
    return render_template('agent/edit.html', 
                         form=form, 
                         agent=agent, 
                         categories=categories,
                         use_cases=use_cases,
                         integration_methods=integration_methods)



@agent_bp.route('/agents')
def list_all():
    """List all agents with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    use_case_id = request.args.get('use_case', type=int)
    integration_id = request.args.get('integration', type=int)
    pricing = request.args.get('pricing')
    
    # Get all categories with counts for sidebar
    categories_with_counts = db.session.query(
        Category,
        func.count(distinct(Agent.id)).label('agent_count')
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
        category.agent_count = count
        categories.append(category)
    
    # Get all use cases with counts for sidebar
    use_cases_with_counts = db.session.query(
        UseCase,
        func.count(Agent.id).label('solution_count')
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
        func.count(Agent.id).label('agent_count')
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
    
    # Base query for agents
    base_query = Agent.query.filter(
        Agent.is_verified == True,
        Agent.status == 'active'
    )
    
    # Apply pricing filter
    if pricing == 'free':
        base_query = base_query.filter(Agent.pricing_info.like('%"model": "free"%'))
    elif pricing == 'paid':
        base_query = base_query.filter(Agent.pricing_info.not_like('%"model": "free"%'))
    
    # Apply category filter if provided
    if category_id:
        base_query = base_query.join(Agent.categories).filter(Category.id == category_id)
    
    # Apply use case filter if provided
    if use_case_id:
        base_query = base_query.join(Agent.use_cases).filter(UseCase.id == use_case_id)
    
    # Apply integration filter if provided
    if integration_id:
        base_query = base_query.join(Agent.integration_method_list).filter(IntegrationMethod.id == integration_id)
    
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
    
    # Get total count before pagination
    total_agents = base_query.count()
    
    # Apply sorting
    if sort == 'newest':
        base_query = base_query.order_by(Agent.created_at.desc())
    elif sort == 'rating':
        # Create a subquery to get average ratings
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
    else:  # default to newest
        base_query = base_query.order_by(Agent.created_at.desc())
    
    # Paginate the results
    pagination = base_query.paginate(
        page=page,
        per_page=27,
        error_out=False 
    )
    
    agents = pagination.items
    
    # Get comprehensive stats
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
    
    # Get category stats for the count
    category_stats = Category.query.all()
    
    # Get featured agents
    featured_agents = Agent.query.filter(
        Agent.is_featured == True,
        Agent.is_verified == True,
        Agent.status == 'active'
    ).order_by(
        func.random()
    ).limit(3).all()  # Limit to 3 featured agents
    
    return render_template('agent/list.html',
                         agents=agents,
                         categories=categories,
                         use_cases=use_cases,  # Add use cases
                         integrations=integrations,  # Add integrations
                         pagination=pagination,
                         total_agents=total_agents,
                         stats=stats,
                         category_stats=category_stats,
                         current_sort=sort,
                         current_search=search,
                         current_category=category_id,
                         featured_agents=featured_agents)

def get_filtered_agents_query(category_id=None, sort_by='newest', search_query=''):
    """Helper function to get filtered agents query"""
    # Start with base query for verified agents only
    query = Agent.query.filter_by(is_verified=True)
    
    # Apply category filter if specified
    if category_id:
        query = query.join(Agent.categories).filter(Category.id == category_id)
    
    # Apply search if specified
    if search_query:
        query = query.filter(
            or_(
                Agent.name.ilike(f'%{search_query}%'),
                Agent.description.ilike(f'%{search_query}%'),
                Agent.provider.ilike(f'%{search_query}%')
            )
        )
    
    # Apply sorting
    if sort_by == 'rating':
        avg_rating = db.session.query(
            Review.agent_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.agent_id).subquery()
        
        query = query.outerjoin(avg_rating, Agent.id == avg_rating.c.agent_id)\
                    .order_by(avg_rating.c.avg_rating.desc().nullslast())
    elif sort_by == 'reviews':
        query = query.order_by(Agent.total_reviews.desc())
    elif sort_by == 'upvotes':
        query = query.order_by(Agent.upvote_count.desc().nullslast())
    else:  # newest
        query = query.order_by(Agent.created_at.desc())
    
    return query

@agent_bp.route('/verify', methods=['GET'])
@login_required
def verify_listings():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    form = FlaskForm()
    unverified_agents = Agent.query.filter_by(is_verified=False).all()
    verified_agents = Agent.query.filter_by(is_verified=True).all()
    featured_agents = Agent.query.filter_by(is_featured=True).order_by(Agent.name).all()
    users = User.query.order_by(User.username).all()
    
    return render_template('admin/verify.html', 
                         unverified_agents=unverified_agents,
                         verified_agents=verified_agents,
                         featured_agents=featured_agents,
                         users=users,
                         form=form)

@agent_bp.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve(id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('main.index'))
        
    agent = Agent.query.get_or_404(id)
    agent.is_verified = True
    agent.status = 'active'
    
    try:
        db.session.commit()
        # Send approval email
        if send_listing_approved_email(agent):
            flash('Agent has been approved and notification email sent.', 'success')
        else:
            flash('Agent has been approved but there was an error sending the notification email.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving agent: {str(e)}', 'error')
        return redirect(url_for('agent.verify_listings'))
        
    return redirect(url_for('agent.verify_listings'))

@agent_bp.route('/<int:id>/unverify', methods=['POST'])
@login_required
def unverify(id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('main.index'))
        
    agent = Agent.query.get_or_404(id)
    agent.is_verified = False
    agent.status = 'pending'  # Set status back to pending when unverified
    agent.is_featured = False  # Also unfeature when unverified
    db.session.commit()
    flash('Agent has been unverified.', 'success')
    return redirect(url_for('agent.verify_listings'))



@agent_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    form = AgentForm()
    categories = Category.query.order_by(Category.display_order).all()
    use_cases = UseCase.query.order_by(UseCase.display_order).all()
    integration_methods = IntegrationMethod.query.order_by(IntegrationMethod.display_order).all()
    
    # Populate choices
    form.categories.choices = [(str(c.id), c.name) for c in categories]
    form.use_cases.choices = [(str(u.id), u.name) for u in use_cases]
    form.integration_methods.choices = [(str(m.id), m.name) for m in integration_methods]
    
    if form.validate_on_submit():
        try:
            # Generate base slug
            base_slug = generate_slug(form.name.data)
            slug = base_slug
            counter = 1
            
            # Ensure unique slug
            while Agent.query.filter_by(slug=slug).first() is not None:
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create new agent instance
            agent = Agent(
                name=form.name.data,
                provider=form.provider.data,
                description=form.description.data,
                short_description=form.short_description.data,
                website=form.website.data,
                api_endpoint=form.api_endpoint.data,
                documentation_url=form.documentation_url.data,
                user_id=current_user.id,
                submitted_by_id=current_user.id,
                is_open_source=form.is_open_source.data,
                source_repository=form.source_repository.data.strip() if form.is_open_source.data and form.source_repository.data else None,
                status='pending',
                is_verified=False,
                slug=slug,
                monthly_users=form.monthly_users.data,
                facebook_url=form.facebook_url.data,
                twitter_url=form.twitter_url.data,
                github_url=form.github_url.data,
                discord_url=form.discord_url.data,  # Add Discord URL
                linkedin_url=form.linkedin_url.data,  # Add LinkedIn URL
                agent_type=form.agent_type.data
            )

            # Handle use cases
            if form.use_cases.data:
                selected_use_case_ids = [int(uc_id) for uc_id in form.use_cases.data]
                selected_use_cases = UseCase.query.filter(UseCase.id.in_(selected_use_case_ids)).all()
                agent.use_cases = selected_use_cases

            # Handle integration methods
            if form.integration_methods.data:
                selected_method_ids = [int(m_id) for m_id in form.integration_methods.data]
                selected_methods = IntegrationMethod.query.filter(IntegrationMethod.id.in_(selected_method_ids)).all()
                agent.integration_method_list = selected_methods

            # Handle logo upload
            if form.logo.data:
                logo_url = save_image(form.logo.data)
                agent.logo_url = logo_url

            # Handle categories
            if form.categories.data:
                selected_category_ids = [int(cat_id) for cat_id in form.categories.data]
                selected_categories = Category.query.filter(Category.id.in_(selected_category_ids)).all()
                agent.categories = selected_categories

            # Handle pricing information
            pricing_info = {
                "model": form.pricing_model.data,
                "free_tier": form.has_free_tier.data,
                "starting_price": form.starting_price.data,
                "price_details": form.price_details.data,
            }
            agent.pricing_info = json.dumps(pricing_info)

            # Handle screenshot
            if form.screenshot.data:
                screenshot_path = save_image(form.screenshot.data)
                agent.screenshot = screenshot_path.split('/')[-1]

            # Add and commit to database
            db.session.add(agent)
            db.session.commit()

            # Send admin notification about new listing
            send_admin_listing_notification(agent)

            flash("Agent submitted successfully! It will be reviewed by our team.", "success")
            return redirect(url_for("agent.detail", slug=agent.slug))

        except Exception as e:
            db.session.rollback()
            print(f"Error submitting agent: {str(e)}")
            flash(f"An error occurred while submitting the agent: {str(e)}", "error")
    else:
        # If form validation failed, print errors
        if form.errors:
            print("Form validation errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", "error")

    return render_template("agent/submit.html", 
                         form=form,
                         categories=categories,
                         use_cases=use_cases,
                         integration_methods=integration_methods)





@agent_bp.route('/<slug>')
def detail(slug):
    agent = Agent.query.filter_by(slug=slug).first_or_404()
    form = ReviewForm()  # Create the form instance
    
    # Track view event
    try:
        agent.view_count = (agent.view_count or 0) + 1
        db.session.commit()
    except Exception as e:
        print(f"Error tracking view: {str(e)}")
        db.session.rollback()
    
    reviews = Review.query\
        .filter_by(agent_id=agent.id)\
        .order_by(Review.created_at.desc())\
        .all()
    
    # Format integration methods if they exist
    try:
        # If it's a string, parse it; if it's already a list, use it
        if isinstance(agent.integration_methods, str):
            methods = json.loads(agent.integration_methods)
        else:
            methods = agent.integration_methods or []
    except:
        methods = []

    # Get similar agents based on categories
    similar_agents = []
    if agent.categories:
        similar_agents = Agent.query\
            .join(AgentCategory)\
            .filter(AgentCategory.category_id.in_([c.id for c in agent.categories]))\
            .filter(Agent.id != agent.id)\
            .filter(Agent.is_verified == True)\
            .distinct()\
            .limit(3)\
            .all()

    return render_template('agent/detail.html',
                         agent=agent,
                         reviews=reviews,
                         form=form,
                         similar_agents=similar_agents,
                         methods=methods)

@agent_bp.route('/search')
def search():
    query = request.args.get('q', '')  # Get the search query
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'rating')

    # Fetch all categories
    all_categories = Category.query.all()

    # Debugging output
    print(f"Search Query: {query}, Category ID: {category_id}, Sort By: {sort_by}")

    # Check if the search route is hit
    if not query:
        print("No search query provided.")
    
    # Base query
    agents = Agent.query.filter_by(status='approved')
    
    # Apply search filters
    if query:
        agents = agents.filter(
            or_(
                Agent.name.ilike(f'%{query}%'),  # Check if name matches
                Agent.description.ilike(f'%{query}%'),  # Check if description matches
                Agent.provider.ilike(f'%{query}%')  # Check if provider matches
            )
        )
        print(f"Filtered agents based on query: {agents.count()} found.")
    
    # Apply category filter
    if category_id:
        agents = agents.join(AgentCategory).filter(AgentCategory.category_id == category_id)
    
    # Apply sorting
    if sort_by == 'rating':
        agents = agents.order_by(Agent.average_rating.desc())
    elif sort_by == 'reviews':
        agents = agents.order_by(Agent.total_reviews.desc())
    elif sort_by == 'newest':
        agents = agents.order_by(Agent.created_at.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    pagination = agents.paginate(page=page, per_page=12, error_out=False)
    
    # Fetch recently added agents (e.g., last 5 added)
    recent_agents = Agent.query.order_by(Agent.created_at.desc()).limit(5).all()
    
    return render_template('agent/search.html',
                         agents=pagination.items,
                         pagination=pagination,
                         query=query,
                         category_id=category_id,
                         sort_by=sort_by,
                         recent_agents=recent_agents,  # Pass recent agents to the template
                         all_categories=all_categories)  # Pass all categories to the template



@agent_bp.route('/api/suggest')
def suggest():
    """API endpoint for autocomplete suggestions"""
    query = request.args.get('q', '')
    suggestions = Agent.query.filter(
        Agent.name.ilike(f'%{query}%')
    ).limit(5).all()
    
    return jsonify([{
        'id': agent.id,
        'name': agent.name,
        'provider': agent.provider,
        'categories': [c.name for c in agent.categories]
    } for agent in suggestions])



@agent_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    agent = Agent.query.get_or_404(id)
    
    # Allow deletion if user is the owner or an admin
    if current_user.id == agent.submitted_by_id or current_user.is_admin:
        try:
            db.session.delete(agent)
            db.session.commit()
            flash('Agent deleted successfully!', 'success')
            
            # If deletion was triggered from admin verification page, return there
            if current_user.is_admin and request.referrer and 'verify' in request.referrer:
                return redirect(url_for('agent.verify_listings'))
            
            # Otherwise return to main page (for regular users)
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting agent: {str(e)}', 'error')
            return redirect(request.referrer or url_for('main.index'))
    else:
        flash('You do not have permission to delete this agent.', 'error')
        return redirect(url_for('agent.detail', slug=agent.slug))

@agent_bp.route('/<int:id>/toggle-verify', methods=['POST'])
@login_required
def toggle_verify(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    agent = Agent.query.get_or_404(id)
    agent.is_verified = not agent.is_verified
    
  
    if agent.is_verified:
        agent.status = 'active'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_verified': agent.is_verified
    })

@agent_bp.route('/<int:id>/toggle-featured', methods=['POST'])
@login_required
def toggle_featured(id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('main.index'))

    agent = Agent.query.get_or_404(id)
    agent.is_featured = not agent.is_featured
    
    # If we're setting as featured, automatically verify and activate
    if agent.is_featured:
        agent.is_verified = True
        agent.status = 'active'
        flash('Agent has been featured and automatically verified.', 'success')
    else:
        flash('Agent has been unfeatured.', 'success')
    
    db.session.commit()
    return redirect(url_for('agent.verify_listings'))


@agent_bp.route('/<int:id>/upvote', methods=['POST'])
@login_required
def upvote(id):
    try:
        agent = Agent.query.get_or_404(id)
        
        # Check if user already upvoted
        existing_upvote = AgentUpvote.query.filter_by(
            user_id=current_user.id,
            agent_id=agent.id
        ).first()
        
        if existing_upvote:
            # Remove upvote
            db.session.delete(existing_upvote)
            agent.upvote_count = max(0, agent.upvote_count - 1)  # Prevent negative counts
            db.session.commit()
            print(f"Removed upvote. New count: {agent.upvote_count}")  # Debug log
        else:
            # Add upvote
            upvote = AgentUpvote(user_id=current_user.id, agent_id=agent.id)
            db.session.add(upvote)
            agent.upvote_count = (agent.upvote_count or 0) + 1  # Handle None value
            db.session.commit()
            print(f"Added upvote. New count: {agent.upvote_count}")  # Debug log
        
        # Refresh the agent object to ensure we have the latest count
        db.session.refresh(agent)
        
        # Return the updated button HTML
        return render_template('agent/_upvote_button.html', agent=agent)
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in upvote: {str(e)}")  # Debug log
        return "Error processing upvote", 500
    

@agent_bp.route('/<int:agent_id>/upvote', methods=['POST'])
@login_required
def toggle_upvote(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    
    if agent in current_user.upvoted_agents:
        current_user.upvoted_agents.remove(agent)
        is_upvoted = False
        message = "Upvote removed"
    else:
        current_user.upvoted_agents.append(agent)
        is_upvoted = True
        message = "Agent upvoted!"
    
    db.session.commit()
    
    return jsonify({
            'success': True,
            'is_upvoted': is_upvoted,
            'message': 'Agent upvoted!' if is_upvoted else 'Upvote removed',
            'upvote_count': agent.upvote_count
        })

@agent_bp.route('/<int:id>/verify', methods=['POST'])
@login_required
def verify(id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('main.index'))
        
    agent = Agent.query.get_or_404(id)
    agent.is_verified = not agent.is_verified
    
    # Automatically set status to active when verified
    if agent.is_verified:
        agent.status = 'active'
        flash('Agent has been verified and activated.', 'success')
    else:
        flash('Agent has been unverified.', 'success')
    
    db.session.commit()
    return redirect(url_for('agent.verify_listings'))

@agent_bp.route('/<int:agent_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(agent_id):
    try:
        agent = Agent.query.get_or_404(agent_id)
        is_favorite = agent.toggle_favorite(current_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_favorite': is_favorite,
            'message': 'Added to locker' if is_favorite else 'Removed from locker'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in toggle_favorite: {str(e)}")  # For debugging
        return jsonify({
            'success': False,
            'message': 'Error updating favorite status'
        }), 500
    


from app.models.user import User  

@agent_bp.route('/change-owner', methods=['POST'])
@login_required
def change_owner():
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Unauthorized. Admin access required.'
        }), 403
    
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        new_owner_email = data.get('new_owner_email')
        
        if not agent_id or not new_owner_email:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        # Find the new owner user
        new_owner = User.query.filter_by(email=new_owner_email).first()
        if not new_owner:
            return jsonify({
                'success': False,
                'message': 'User not found with that email'
            }), 404
        
        # Find and update the agent
        agent = Agent.query.get(agent_id)
        if not agent:
            return jsonify({
                'success': False,
                'message': 'Agent not found'
            }), 404
        
        # Update both owner and email
        agent.user_id = new_owner.id
        agent.email = new_owner.email
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Owner changed to {new_owner.email}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error changing owner: {str(e)}")  # For debugging
        return jsonify({
            'success': False,
            'message': 'Error changing owner'
        }), 500

@agent_bp.route('/integrations/<slug>')
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
        # Create a subquery to get average ratings
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
                         form=form,
                         featured_agents=featured_agents)

@agent_bp.route('/<int:agent_id>/track/<event_type>', methods=['POST'])
def track_event(agent_id, event_type):
    """Track analytics events for agents"""
    try:
        agent = Agent.query.get_or_404(agent_id)
        data = request.get_json()
        source_page = data.get('source_page', '')
        
        # Update agent counters
        if event_type == 'impression':
            agent.impression_count = (agent.impression_count or 0) + 1
        elif event_type == 'view':
            agent.view_count = (agent.view_count or 0) + 1
        elif event_type == 'click':
            agent.click_count = (agent.click_count or 0) + 1
            
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error tracking {event_type}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
