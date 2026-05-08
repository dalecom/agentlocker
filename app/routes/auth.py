from flask import Blueprint, render_template, redirect, url_for, flash, request, flash, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils.helpers import send_verification_email, generate_verification_token, send_admin_verification_notification
from werkzeug.security import generate_password_hash
from app.forms import LoginForm
from app.forms import RegisterForm
from werkzeug.utils import secure_filename
import os
from app.models.agent import Agent
from app.models.review import Review
import time
from flask_wtf import FlaskForm
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode
import io
import base64
from app.forms import Setup2FAForm
from app.forms import Verify2FAForm
from flask_mail import Message
from app import mail  
from sqlalchemy import func

class AvatarForm(FlaskForm):
    pass  # We only need this for CSRF protection

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/check-username')
def check_username():
    username = request.args.get('username')
    if not username:
        return jsonify({'available': False})
        
    # Check if username exists
    user = User.query.filter(func.lower(User.username) == func.lower(username)).first()
    return jsonify({'available': user is None})

@auth_bp.route('/check-email')
def check_email():
    email = request.args.get('email')
    if not email:
        return jsonify({'available': False})
        
    # Check if email exists
    user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
    return jsonify({'available': user is None})



@auth_bp.route('/profile')
@login_required
def profile():
    form = AvatarForm()  # Create form instance for CSRF token
    # Get user's agents
    user_agents = Agent.query.filter_by(user_id=current_user.id).all()
    
    # Get user's reviews
    user_reviews = Review.query.filter_by(user_id=current_user.id).all()
    
    return render_template('auth/profile.html', 
                         user=current_user,
                         agents=user_agents,
                         reviews=user_reviews,
                         form=form)



# Add these helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


from app.utils.helpers import save_image  

@auth_bp.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    if 'avatar' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('auth.profile'))
    
    file = request.files['avatar']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('auth.profile'))
    
    if file and allowed_file(file.filename):
        try:
            # Use the save_image helper function
            avatar_url = save_image(file, folder='uploads/avatars')
            if avatar_url:
                # Extract just the filename from the URL
                filename = os.path.basename(avatar_url)
                current_user.avatar = filename
                db.session.commit()
                flash('Profile picture updated successfully!', 'success')
            else:
                current_app.logger.error("save_image returned None")
                flash('Error saving image', 'error')
        except Exception as e:
            current_app.logger.error(f"Error updating avatar: {str(e)}")
            current_app.logger.exception("Full traceback:")  # This will log the full stack trace
            flash('Error updating profile picture', 'error')
    else:
        flash('Invalid file type', 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data,
                       email=form.email.data,
                       full_name=form.full_name.data,
                       is_verified=False)  # Explicitly set as unverified
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            # Generate token and send verification email
            token = user.get_verification_token()
            send_verification_email(user.email, token)
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('auth.register'))
            
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Allow admins to log in without verification
            if not user.is_verified and not user.is_admin:
                flash('Please verify your email address first. Check your inbox for the verification link.', 'warning')
                # Resend verification email
                send_verification_email(user)
                return redirect(url_for('auth.login'))
                
            if user.two_factor_enabled:
                session['user_id'] = user.id
                session['email'] = user.email
                return redirect(url_for('auth.verify_2fa'))
            
            login_user(user)
            return redirect(url_for('main.index'))
            
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        
        if user:
            token = generate_verification_token(user.email)
            user.reset_token = token
            db.session.commit()
            
            # Send password reset email
            send_password_reset_email(user.email, token)
            
        flash('If an account exists with this email, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user:
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        user.password_hash = generate_password_hash(request.form['password'])
        user.reset_token = None
        db.session.commit()
        
        flash('Password reset successful! You can now login with your new password.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html')



@auth_bp.route('/user/<username>')
def public_profile(username):
    """Public profile view for any user"""
    # Get user or return 404
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get user's verified agents
    user_agents = Agent.query.filter_by(
        user_id=user.id,
        is_verified=True
    ).order_by(Agent.created_at.desc()).all()
    
    # Get user's reviews
    user_reviews = Review.query.filter_by(
        user_id=user.id
    ).order_by(Review.created_at.desc()).all()
    
    return render_template('auth/public_profile.html',
                         user=user,
                         agents=user_agents,
                         reviews=user_reviews)


@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if not current_user.check_password(request.form.get('current_password')):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        # Basic profile updates
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.bio = request.form.get('bio')
        
        # Social links and website
        # Clean up URLs by ensuring they start with http:// or https://
        website = request.form.get('website', '').strip()
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        current_user.website = website if website else None
        
        # Twitter handle - store without @ symbol
        twitter = request.form.get('twitter', '').strip().lstrip('@')
        current_user.twitter = twitter if twitter else None
        
        # GitHub URL
        github = request.form.get('github', '').strip()
        if github and not github.startswith(('http://', 'https://')):
            github = 'https://' + github
        current_user.github = github if github else None
        
        # Handle password change if new password is provided
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating profile: {str(e)}")
        db.session.rollback()
        flash('Error updating profile', 'error')
        
    return redirect(url_for('auth.profile'))



@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    form = Setup2FAForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        code = form.code.data
        totp = pyotp.TOTP(current_user.two_factor_secret)
        
        if totp.verify(code):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash('Two-factor authentication enabled successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Invalid verification code', 'error')
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(current_user.get_2fa_uri())
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    
    return render_template('auth/setup_2fa.html', 
                         form=form, 
                         qr_code=qr_code, 
                         secret=current_user.two_factor_secret)

@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'user_id' not in session and 'email' not in session:
        return redirect(url_for('auth.login'))
    
    form = Verify2FAForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        code = form.code.data
        
        # Try to get user by ID first, then by email
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
        if user is None and 'email' in session:
            user = User.query.filter_by(email=session['email']).first()
        
        if not user:
            return redirect(url_for('auth.login'))
        
        totp = pyotp.TOTP(user.two_factor_secret)
        
        if totp.verify(code):
            login_user(user)
            # Clean up session
            session.pop('user_id', None)
            session.pop('email', None)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid verification code', 'error')
    
    return render_template('auth/verify_2fa.html', form=form)

@auth_bp.route('/disable-2fa', methods=['GET'])
@login_required
def disable_2fa():
    if current_user.two_factor_enabled:
        current_user.two_factor_enabled = False
        current_user.two_factor_secret = None
        db.session.commit()
        flash('Two-factor authentication has been disabled.', 'success')
    else:
        flash('Two-factor authentication is not enabled.', 'warning')
    
    return redirect(url_for('auth.profile'))

def send_verification_email(user):
    token = user.get_verification_token()
    msg = Message('Verify Your Email - Agent Locker',
                  sender=("Agent Locker", "team@agentlocker.ai"),
                  recipients=[user.email])
    msg.html = render_template('auth/email/verify_email.html',
                             user=user, token=token)
    mail.send(msg)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for('main.index'))
        
    user = User.verify_email_token(token)
    if not user:
        flash('The verification link is invalid or has expired.', 'error')
        return redirect(url_for('auth.login'))
        
    try:
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        db.session.commit()
        
        # Send admin notification after successful verification
        try:
            send_admin_verification_notification(user)
        except Exception as e:
            current_app.logger.error(f"Error sending admin notification: {str(e)}")
            # Don't fail the verification if notification fails
            
        flash('Email verification successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during email verification: {str(e)}")
        flash('An error occurred during verification. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/verify-admin/<int:id>', methods=['POST'])
@login_required
def verify_admin(id):
    # Only allow admins to verify other users
    if not current_user.is_admin:
        flash('You do not have permission to verify users.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    user.is_verified = True
    user.email_verified_at = datetime.utcnow()
    
    try:
        db.session.commit()
        # Send admin notification after successful verification
        send_admin_verification_notification(user)
        flash(f'User {user.username} has been verified.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during admin verification: {str(e)}")
        flash('An error occurred during verification. Please try again.', 'error')
        
    return redirect(url_for('user.manage_users'))