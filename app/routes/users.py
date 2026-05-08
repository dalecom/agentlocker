from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User  # Adjust the import based on your structure

user_bp = Blueprint('user', __name__)

@user_bp.route('/manage_users', methods=['GET'])
@login_required
def manage_users():
    # Ensure only admins can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    users = User.query.all()  # Fetch all users
    return render_template('admin/manage_users.html', users=users)

@user_bp.route('/change_status/<int:id>', methods=['POST'])
@login_required
def change_status(id):
    # Ensure only admins can change user status
    if not current_user.is_admin:
        flash('You do not have permission to modify user status.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    
    # Prevent changing own status
    if user.id == current_user.id:
        flash('You cannot modify your own status.', 'warning')
        return redirect(url_for('user.manage_users'))
    
    try:
        # Get form data
        is_admin = request.form.get('is_admin') == '1'
        
        # Update user status
        user.is_admin = is_admin
        db.session.commit()
        flash(f'User {user.username} role updated successfully.', 'success')
        return redirect(url_for('user.manage_users'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating user role.', 'error')
        return redirect(url_for('user.manage_users'))