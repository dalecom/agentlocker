from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.category import Category
from app.forms import CategoryForm
from app.extensions import db  # Changed this line
from slugify import slugify
from functools import wraps
from app.models.user import User
from app.models.use_case import UseCase
from app.forms import UseCaseForm  # We'll create this next
from app.models.integration_method import IntegrationMethod
from app.forms import IntegrationMethodForm
from app.models.blog import BlogPost, BlogCategory
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app.forms import BlogPostForm  # Add this import
from app.models.agent import Agent
from flask_mail import Message
from app.extensions import mail


admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/categories', methods=['GET'])
@login_required
def manage_categories():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))
        
    categories = Category.query.order_by(Category.display_order, Category.name).all()
    form = CategoryForm()
    return render_template('admin/categories.html', categories=categories, form=form)

@admin_bp.route('/categories/create', methods=['POST'])
@login_required
def create_category():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            slug=slugify(form.name.data),
            description=form.description.data,
            icon=form.icon.data,
            color=form.color.data,
            display_order=form.display_order.data
        )
        db.session.add(category)
        try:
            db.session.commit()
            flash('Category created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error creating category. Please try again.', 'error')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    category = Category.query.get_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    

@admin_bp.route('/categories/<int:category_id>', methods=['GET'])
@login_required
def get_category(category_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    category = Category.query.get_or_404(category_id)
    return jsonify({
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'icon': category.icon,
        'color': category.color,
        'display_order': category.display_order
    })

@admin_bp.route('/categories/<int:category_id>/edit', methods=['POST'])
@login_required
def edit_category(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to edit categories.', 'error')
        return redirect(url_for('main.index'))

    category = Category.query.get_or_404(category_id)
    form = CategoryForm()

    if form.validate_on_submit():
        try:
            category.name = form.name.data
            category.description = form.description.data
            category.icon = form.icon.data
            category.color = form.color.data
            category.display_order = form.display_order.data
            category.slug = form.slug.data if form.slug.data else slugify(form.name.data)
            
            db.session.commit()
            flash('Category updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating category. Please try again.', 'error')
            
    return redirect(url_for('admin.manage_categories'))


@admin_bp.route('/user/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/use-cases')
@login_required
@admin_required
def use_cases():
    use_cases = UseCase.query.order_by(UseCase.display_order).all()
    form = UseCaseForm()
    return render_template('admin/use_cases.html', use_cases=use_cases, form=form)

@admin_bp.route('/use-cases', methods=['POST'])
@login_required
@admin_required
def create_use_case():
    form = UseCaseForm()
    if form.validate_on_submit():
        try:
            # Generate slug if not provided
            slug = form.slug.data if form.slug.data else slugify(form.name.data)
            
            use_case = UseCase(
                name=form.name.data,
                slug=slug,
                description=form.description.data,
                icon=form.icon.data,
                color=form.color.data,
                display_order=form.display_order.data
            )
            db.session.add(use_case)
            db.session.commit()
            flash('Use case created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating use case: {str(e)}', 'error')
            print(f"Error creating use case: {str(e)}")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
            print(f"Form validation errors: {form.errors}")
    return redirect(url_for('admin.use_cases'))

@admin_bp.route('/use-cases/<int:id>')
@login_required
@admin_required
def get_use_case(id):
    use_case = UseCase.query.get_or_404(id)
    return jsonify({
        'id': use_case.id,
        'name': use_case.name,
        'slug': use_case.slug,
        'description': use_case.description,
        'icon': use_case.icon,
        'color': use_case.color,
        'display_order': use_case.display_order
    })

@admin_bp.route('/use-cases/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_use_case(id):
    use_case = UseCase.query.get_or_404(id)
    form = UseCaseForm()
    if form.validate_on_submit():
        try:
            use_case.name = form.name.data
            # Update slug if provided, otherwise generate from name
            use_case.slug = form.slug.data if form.slug.data else slugify(form.name.data)
            use_case.description = form.description.data
            use_case.icon = form.icon.data
            use_case.color = form.color.data
            use_case.display_order = form.display_order.data
            db.session.commit()
            flash('Use case updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating use case: {str(e)}', 'error')
    return redirect(url_for('admin.use_cases'))

@admin_bp.route('/use-cases/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_use_case(id):
    use_case = UseCase.query.get_or_404(id)
    db.session.delete(use_case)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/integration-methods')
@login_required
@admin_required
def integration_methods():
    methods = IntegrationMethod.query.order_by(IntegrationMethod.display_order).all()
    form = IntegrationMethodForm()
    return render_template('admin/integration_methods.html', integration_methods=methods, form=form)

@admin_bp.route('/integration-methods', methods=['POST'])
@login_required
@admin_required
def create_integration_method():
    form = IntegrationMethodForm()
    if form.validate_on_submit():
        try:
            # Generate slug if not provided
            slug = form.slug.data if form.slug.data else slugify(form.name.data)
            
            method = IntegrationMethod(
                name=form.name.data,
                slug=slug,
                description=form.description.data,
                icon=form.icon.data,
                color=form.color.data,
                display_order=form.display_order.data
            )
            db.session.add(method)
            db.session.commit()
            flash('Integration method created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating integration method: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
    return redirect(url_for('admin.integration_methods'))

@admin_bp.route('/integration-methods/<int:id>')
@login_required
@admin_required
def get_integration_method(id):
    method = IntegrationMethod.query.get_or_404(id)
    return jsonify({
        'id': method.id,
        'name': method.name,
        'slug': method.slug,
        'description': method.description,
        'icon': method.icon,
        'color': method.color,
        'display_order': method.display_order
    })

@admin_bp.route('/integration-methods/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_integration_method(id):
    method = IntegrationMethod.query.get_or_404(id)
    form = IntegrationMethodForm()
    if form.validate_on_submit():
        try:
            method.name = form.name.data
            # Update slug if provided, otherwise generate from name
            method.slug = form.slug.data if form.slug.data else slugify(form.name.data)
            method.description = form.description.data
            method.icon = form.icon.data
            method.color = form.color.data
            method.display_order = form.display_order.data
            db.session.commit()
            flash('Integration method updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating integration method: {str(e)}', 'error')
    return redirect(url_for('admin.integration_methods'))

@admin_bp.route('/integration-methods/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_integration_method(id):
    method = IntegrationMethod.query.get_or_404(id)
    db.session.delete(method)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/blog/posts')
@login_required
@admin_required
def blog_posts():
    """Admin blog posts listing."""
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    categories = BlogCategory.query.all()  # Add this line to get categories
    return render_template('admin/blog/posts.html', posts=posts, categories=categories)

@admin_bp.route('/blog/post/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_blog_post():
    form = BlogPostForm()
    
    # Populate category choices from BlogCategory model
    form.category_id.choices = [
        (c.id, c.name) for c in BlogCategory.query.order_by(BlogCategory.name).all()
    ]
    
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            slug=form.slug.data,
            content=form.content.data,
            excerpt=form.excerpt.data,
            published=form.published.data,
            featured=form.featured.data,
            category_id=form.category_id.data,
            author_id=current_user.id
        )
        
        if form.featured_image.data:
            # Handle image upload
            filename = secure_filename(form.featured_image.data.filename)
            # Generate unique filename
            unique_filename = f"featured-{datetime.now().strftime('%Y%m%d%H%M%S')}-{filename}"
            # Create blog uploads directory if it doesn't exist
            blog_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog')
            os.makedirs(blog_upload_dir, exist_ok=True)
            # Save the file
            filepath = os.path.join(blog_upload_dir, unique_filename)
            form.featured_image.data.save(filepath)
            # Set the image URL with the proper path
            post.image_url = f"/static/uploads/blog/{unique_filename}"
            
        db.session.add(post)
        db.session.commit()
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin.blog_posts'))
        
    return render_template('admin/blog/post_form.html', form=form, title='New Blog Post')

@admin_bp.route('/blog/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blog_post(id):
    post = BlogPost.query.get_or_404(id)
    form = BlogPostForm(obj=post)
    
    # Populate category choices from BlogCategory model
    form.category_id.choices = [
        (c.id, c.name) for c in BlogCategory.query.order_by(BlogCategory.name).all()
    ]
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = form.slug.data
        post.content = form.content.data
        post.excerpt = form.excerpt.data
        post.published = form.published.data
        post.featured = form.featured.data
        post.category_id = form.category_id.data
        
        if form.featured_image.data:
            # Handle image upload
            filename = secure_filename(form.featured_image.data.filename)
            # Generate unique filename
            unique_filename = f"featured-{datetime.now().strftime('%Y%m%d%H%M%S')}-{filename}"
            # Create blog uploads directory if it doesn't exist
            blog_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog')
            os.makedirs(blog_upload_dir, exist_ok=True)
            # Save the file
            filepath = os.path.join(blog_upload_dir, unique_filename)
            form.featured_image.data.save(filepath)
            # Set the image URL with the proper path
            post.image_url = f"/static/uploads/blog/{unique_filename}"
            
        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin.blog_posts'))
        
    return render_template('admin/blog/post_form.html', form=form, post=post, title='Edit Blog Post')

@admin_bp.route('/blog/post/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_blog_post(id):
    """Delete a blog post."""
    post = BlogPost.query.get_or_404(id)
    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/upload/ckeditor', methods=['POST'])
@login_required
@admin_required
def upload_ckeditor_image():
    current_app.logger.info('CKEditor upload request received')
    current_app.logger.info(f'Files in request: {request.files}')
    current_app.logger.info(f'Headers: {dict(request.headers)}')
    
    if 'upload' not in request.files:
        current_app.logger.error('No upload file in request')
        return jsonify({'error': {'message': 'No file part'}}), 400
        
    file = request.files['upload']
    current_app.logger.info(f'Received file: {file.filename}')
    
    if file.filename == '':
        current_app.logger.error('Empty filename')
        return jsonify({'error': {'message': 'No selected file'}}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Create blog uploads directory if it doesn't exist
            blog_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog')
            os.makedirs(blog_upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(f"content-{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
            
            # Save the file
            filepath = os.path.join(blog_upload_dir, filename)
            file.save(filepath)
            
            url = f'/static/uploads/blog/{filename}'
            current_app.logger.info(f'File saved successfully: {url}')
            
            return jsonify({
                'url': url
            })
            
        except Exception as e:
            current_app.logger.error(f'Error saving file: {str(e)}')
            return jsonify({'error': {'message': str(e)}}), 500
    
    current_app.logger.error('Invalid file type')
    return jsonify({'error': {'message': 'Invalid file type'}}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/blog/categories')
@login_required
def get_blog_categories():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    categories = BlogCategory.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'icon': c.icon,
        'color': c.color,
        'post_count': c.posts.count()
    } for c in categories])

@admin_bp.route('/blog/category', methods=['POST'])
@admin_bp.route('/blog/category/<int:id>', methods=['PUT'])
@login_required
def save_blog_category(id=None):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    try:
        if id:
            # Update existing category
            category = BlogCategory.query.get_or_404(id)
            category.name = data['name']
            category.description = data.get('description')
            category.icon = data.get('icon')
            category.color = data.get('color')  # Add color handling
        else:
            # Create new category
            category = BlogCategory(
                name=data['name'],
                description=data.get('description'),
                icon=data.get('icon'),
                color=data.get('color')  # Add color handling
            )
            db.session.add(category)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'icon': category.icon,
                'color': category.color,  # Include color in response
                'post_count': category.posts.count()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/blog/category/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_blog_category(id):
    """Delete a blog category."""
    category = BlogCategory.query.get_or_404(id)
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/sales')
@login_required
def sales():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # Default to 50 items
    
    # Validate per_page to only allow specific values
    allowed_page_sizes = [10, 20, 50, 100, 500]
    if per_page not in allowed_page_sizes:
        per_page = 50
    
    # Get sort parameters
    sort_by = request.args.get('sort', 'name')
    sort_dir = request.args.get('dir', 'asc')
    
    # List of emails to exclude
    excluded_emails = [
        'team@agentlocker.ai',
        'david.black@dcblack.co.uk',
        'nabiamin159@gmail.com',
        'ennersmai@gmail.com',
        'mohsinasifaly@gmail.com',
        'jaymathenge7@gmail.com'
    ]
    
    # List of demo featured agents to exclude from stats
    demo_featured_agents = ['Superagent', 'AgentGPT', 'BabyAGI']
    
    # Base query
    query = Agent.query.filter_by(is_verified=True)
    
    # Calculate statistics excluding demo agents
    stats = {
        'total_agents': Agent.query.filter_by(
            is_verified=True
        ).filter(~Agent.name.in_(demo_featured_agents)).count(),
        
        'total_uncontacted': Agent.query.filter_by(
            is_verified=True, 
            contacted=False
        ).filter(~Agent.name.in_(demo_featured_agents)).count(),
        
        'total_contacted': Agent.query.filter_by(
            is_verified=True, 
            contacted=True, 
            pitched_ads=False
        ).filter(~Agent.name.in_(demo_featured_agents)).count(),
        
        'total_pitched': Agent.query.filter_by(
            is_verified=True, 
            contacted=True, 
            pitched_ads=True,
            is_featured=False
        ).filter(~Agent.name.in_(demo_featured_agents)).count(),
        
        'total_converted': Agent.query.filter_by(
            is_verified=True,
            is_featured=True
        ).filter(~Agent.name.in_(demo_featured_agents)).count(),
        
        'total_emails_sent': Agent.query.filter_by(
            is_verified=True,
            sales_email_sent=True
        ).filter(~Agent.name.in_(demo_featured_agents)).count()
    }
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(Agent.name.asc() if sort_dir == 'asc' else Agent.name.desc())
    elif sort_by == 'email':
        query = query.order_by(Agent.email.asc() if sort_dir == 'asc' else Agent.email.desc())
    elif sort_by == 'added_on_x':
        query = query.order_by(Agent.added_on_x.asc() if sort_dir == 'asc' else Agent.added_on_x.desc())
    elif sort_by == 'contacted':
        query = query.order_by(Agent.contacted.asc() if sort_dir == 'asc' else Agent.contacted.desc())
    elif sort_by == 'pitched_ads':
        query = query.order_by(Agent.pitched_ads.asc() if sort_dir == 'asc' else Agent.pitched_ads.desc())
    elif sort_by == 'is_featured':
        query = query.order_by(Agent.is_featured.asc() if sort_dir == 'asc' else Agent.is_featured.desc())
    elif sort_by == 'sales_email_sent':
        query = query.order_by(Agent.sales_email_sent.asc() if sort_dir == 'asc' else Agent.sales_email_sent.desc())
    elif sort_by == 'twitter_handle':
        query = query.order_by(Agent.twitter_url.asc() if sort_dir == 'asc' else Agent.twitter_url.desc())
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    agents = pagination.items
    
    # Pre-populate emails from owners if not in excluded list
    for agent in agents:
        if (agent.owner and 
            agent.owner.email and 
            agent.owner.email not in excluded_emails and 
            not agent.email):
            agent.email = agent.owner.email
            
    db.session.commit()
    
    return render_template('admin/sales.html', 
                         agents=agents,
                         pagination=pagination,
                         per_page=per_page,
                         current_sort=sort_by, 
                         current_dir=sort_dir,
                         stats=stats)

@admin_bp.route('/sales/update-email/<int:agent_id>', methods=['POST'])
@login_required
def update_email(agent_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        agent = Agent.query.options(db.joinedload(Agent.owner)).get_or_404(agent_id)
        
        # Update the email
        new_email = data.get('email', '').strip()
        agent.email = new_email if new_email else None
        
        # Check if email matches owner's email
        is_verified = bool(agent.owner and agent.owner.email and agent.email == agent.owner.email)
        
        # Commit the change
        db.session.commit()
        
        return jsonify({
            'success': True,
            'verified': is_verified,
            'message': 'Email updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/sales/update-x-status/<int:agent_id>', methods=['POST'])
@login_required
def update_x_status(agent_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        agent = Agent.query.get_or_404(agent_id)
        agent.added_on_x = data.get('status')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/sales/toggle-status/<int:agent_id>', methods=['POST'])
@login_required
def toggle_status(agent_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        field = data.get('field')
        agent = Agent.query.get_or_404(agent_id)
        
        if field == 'contacted':
            agent.contacted = not agent.contacted
            new_status = agent.contacted
        elif field == 'pitched_ads':
            agent.pitched_ads = not agent.pitched_ads
            new_status = agent.pitched_ads
        elif field == 'is_featured':
            agent.is_featured = not agent.is_featured
            new_status = agent.is_featured
            
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/sales/send-feature-email/<int:agent_id>', methods=['POST'])
@login_required
def send_feature_email(agent_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    try:
        agent = Agent.query.get_or_404(agent_id)
        if not agent.email:
            return jsonify({'success': False, 'message': 'No email address available'}), 400
            
        # Get next month's name
        next_month = (datetime.now() + timedelta(days=32)).strftime('%B')
        
        # Prepare email content
        html_content = render_template('auth/email/sales_feature_offer.html',
                                     agent=agent,
                                     next_month=next_month,
                                     monthly_views="10,000")
        
        msg = Message(
            subject=f"Feature Your AI Agent '{agent.name}' on Agent Locker",
            sender=("Agent Locker", "team@agentlocker.ai"),
            recipients=[agent.email]
        )
        msg.html = html_content
        
        mail.send(msg)
        
        # Update agent's status
        agent.contacted = True
        agent.sales_email_sent = True
        agent.sales_email_sent_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Email sent successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500