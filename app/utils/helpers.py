import os
import jwt
from PIL import Image
from datetime import datetime, timedelta
from flask import current_app, url_for, render_template
from werkzeug.utils import secure_filename
import uuid
from slugify import slugify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Message
from app import mail

def generate_slug(text):
    return slugify(str(text))  # Convert to str explicitly

def save_image(file, folder='uploads', quality=80):
    """Save an uploaded image as WebP and return its URL"""
    if not file:
        return None
        
    # Create upload folder if it doesn't exist
    upload_folder = os.path.join(current_app.static_folder, folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    filename_without_ext = os.path.splitext(original_filename)[0]
    unique_filename = f"{uuid.uuid4()}_{filename_without_ext}.webp"
    filepath = os.path.join(upload_folder, unique_filename)
    
    # Save and optimize image
    image = Image.open(file)
    
    # Convert RGBA to RGB if necessary
    if image.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # Resize if too large
    image.thumbnail((800, 800))
    
    # Save as WebP
    image.save(filepath, 'WEBP', quality=quality)
    
    return f"/static/{folder}/{unique_filename}"

def generate_slug(text):
    """Generate a URL-friendly slug from text"""
    return slugify(text)

def generate_verification_token(email):
    """Generate a timed JWT token for email verification"""
    token = jwt.encode(
        {
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=1)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return token

def verify_token(token):
    """Verify a JWT token and return the email"""
    try:
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return data['email']
    except:
        return None

def send_email(to_email, subject, html_content):
    """Send an email using SMTP"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = to_email
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    try:
        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
                server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_verification_email(user):
    """Send email verification link"""
    token = user.get_verification_token()
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    html_content = render_template('auth/email/verify_email.html', verification_url=verification_url)
    
    msg = Message('Verify your email - Agent Locker',
                  sender=("Agent Locker", "team@agentlocker.ai"),
                  recipients=[user.email])
    msg.html = html_content
    mail.send(msg)
    return True

def send_password_reset_email(email, token):
    """Send password reset link"""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    html_content = render_template('email/reset_password.html', reset_url=reset_url)
    return send_email(email, 'Reset your password', html_content)

def format_datetime(value, format='medium'):
    """Format a datetime object for display"""
    if format == 'full':
        format = "%A, %B %d, %Y at %I:%M %p"
    elif format == 'medium':
        format = "%B %d, %Y"
    elif format == 'short':
        format = "%b %d, %Y"
    return value.strftime(format)

def send_listing_approved_email(agent):
    """Send email notification when a listing is approved"""
    if not agent.submitter or not agent.submitter.email:
        return False
        
    html_content = render_template('auth/email/listing_approved.html', agent=agent)
    
    msg = Message(
        subject=f"Your AI Agent '{agent.name}' has been approved!",
        sender=("Agent Locker", "team@agentlocker.ai"),
        recipients=[agent.owner.email]
    )
    msg.html = html_content
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send approval email: {e}")
        return False

def send_admin_verification_notification(user):
    """Send notification to admin when a user verifies their email"""
    try:
        msg = Message(
            'New User Verified - Agent Locker',
            sender=("Agent Locker", "team@agentlocker.ai"),
            recipients=['team@agentlocker.ai']
        )
        msg.html = render_template('auth/email/admin_user_verified.html', user=user)
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send admin verification notification: {e}")
        return False

def send_admin_listing_notification(agent):
    """Send notification to admin when a new listing is submitted"""
    html_content = render_template('auth/email/admin_new_listing.html', agent=agent)
    
    msg = Message(
        subject=f"New AI Agent Listing: {agent.name}",
        sender=("Agent Locker", "team@agentlocker.ai"),
        recipients=["team@agentlocker.ai"]
    )
    msg.html = html_content
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send admin listing notification: {e}")
        return False