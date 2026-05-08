from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectMultipleField, PasswordField, SelectField
from wtforms.validators import DataRequired, URL, Optional, Email, Length, ValidationError, EqualTo
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, DataRequired, Email, Optional
from wtforms.widgets import ListWidget, CheckboxInput
from app.models.user import User


class ReviewForm(FlaskForm):
    rating = IntegerField('Rating', validators=[
        DataRequired(),
        NumberRange(min=1, max=5, message='Rating must be between 1 and 5')
    ])
    review_text = TextAreaField('Review', validators=[
        DataRequired(),
        Length(min=10, max=1000, message='Review must be between 10 and 1000 characters')
    ])

class AgentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    provider = StringField('Provider', validators=[DataRequired()])
    agent_type = SelectField(
        'Agent Type',
        choices=[
            ('agentic', 'Agentic AI'),
            ('tool', 'AI Tool'),
            ('platform', 'Agent Platform')
        ],
        default='agentic',
        validators=[DataRequired()]
    )
    description = TextAreaField('Description', validators=[DataRequired()])
    short_description = StringField('Short Description', validators=[
        DataRequired(),
        Length(max=110, message='Short description must be 110 characters or less')
    ])
    website = StringField('Website', validators=[DataRequired(), URL()])
    api_endpoint = StringField('API Endpoint', validators=[Optional()])
    documentation_url = StringField('Documentation URL', validators=[Optional(), URL()])
    logo = FileField('Logo', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    facebook_url = StringField('Facebook URL', 
        validators=[Optional(), URL()],
        description='Link to Facebook page')
    twitter_url = StringField('X (Twitter) URL', 
        validators=[Optional(), URL()],
        description='Link to X/Twitter profile')
    github_url = StringField('GitHub URL', 
        validators=[Optional(), URL()],
        description='Link to GitHub repository')
    discord_url = StringField('Discord URL', 
        validators=[Optional(), URL()],
        description='Link to Discord server')
    linkedin_url = StringField('LinkedIn URL', 
        validators=[Optional(), URL()],
        description='Link to LinkedIn profile')
    use_cases = SelectMultipleField('Use Cases',
        choices=[],  # This will be populated dynamically
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
        validators=[
            Length(max=5, message='Please select no more than 5 use cases')
        ]
    )
    integration_methods = SelectMultipleField('Integration Methods',
        choices=[
            # API Types
            ('rest_api', 'REST API'),
            ('graphql', 'GraphQL API'),
            ('websocket', 'WebSocket API'),
            ('grpc', 'gRPC API'),
            ('streaming_api', 'Streaming API'),
            
            # Development Tools
            ('github_copilot', 'GitHub Integration'),
            ('vscode_extension', 'VS Code Extension'),
            ('jupyter_notebook', 'Jupyter Notebook'),
            ('docker_container', 'Docker Container'),
            ('cli_tool', 'Command Line Tool'),
            
            # SDKs & Libraries
            ('python_sdk', 'Python SDK'),
            ('javascript_sdk', 'JavaScript SDK'),
            ('node_sdk', 'Node.js SDK'),
            ('java_sdk', 'Java SDK'),
            ('go_sdk', 'Go SDK'),
            
            # Platform Integrations
            ('slack_bot', 'Slack Integration'),
            ('discord_bot', 'Discord Bot'),
            ('teams_app', 'Microsoft Teams'),
            ('telegram_bot', 'Telegram Bot'),
            ('whatsapp_api', 'WhatsApp Business API'),
            
            # No-Code Platforms
            ('zapier', 'Zapier Integration'),
            ('make_com', 'Make.com (Integromat)'),
            ('bubble_io', 'Bubble.io Plugin'),
            ('airtable', 'Airtable Extension'),
            ('webflow', 'Webflow Integration'),
            
            # Cloud Platforms
            ('aws_lambda', 'AWS Lambda'),
            ('gcp_functions', 'Google Cloud Functions'),
            ('azure_functions', 'Azure Functions'),
            ('vercel', 'Vercel Integration'),
            ('cloudflare_workers', 'Cloudflare Workers'),
            
            # Development Platforms
            ('android_sdk', 'Android SDK'),
            ('ios_sdk', 'iOS SDK'),
            ('chrome_extension', 'Chrome Extension'),
            ('wordpress_plugin', 'WordPress Plugin'),
            ('shopify_app', 'Shopify App'),
            
            # Enterprise Solutions
            ('enterprise_api', 'Enterprise API'),
            ('saas_integration', 'SaaS Integration'),
            ('single_sign_on', 'SSO Support'),
            ('api_gateway', 'API Gateway'),
            ('vpn_access', 'VPN Access'),

            # No code
            ('website_browser', 'Website / Browser'),
            ('no_code', 'No Code'),
            
            # Direct Integrations
            ('iframe_embed', 'iFrame Embedding'),
            ('js_widget', 'JavaScript Widget'),
            ('api_proxy', 'API Proxy'),
            ('white_label', 'White Label Solution'),
            ('custom_integration', 'Custom Integration')
        ],
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
        validators=[
            Length(max=10, message='Please select no more than 10 integration methods')
        ]
    )
    pricing_model = SelectField(
        'Pricing Model',
        choices=[
            ('free', 'Free'),
            ('freemium', 'Freemium'),
            ('subscription', 'Subscription-based'),
            ('usage', 'Usage-based / Pay-as-you-go'),
            ('enterprise', 'Enterprise / Custom Pricing'),
            ('one_time', 'One-time Purchase'),
            ('other', 'Other')
        ],
        validators=[DataRequired()]
    )
    has_free_tier = BooleanField('Free Tier Available')
    starting_price = StringField('Starting Price', validators=[Optional()])
    price_details = TextAreaField('Price Details', validators=[Optional()])
    categories = SelectMultipleField('Categories',
        choices=[],  # This will be populated dynamically
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
        validators=[
            DataRequired(),
            Length(max=5, message='Please select no more than 5 categories')
        ]
    )
    monthly_users = IntegerField('Monthly Users', 
                                validators=[Optional()],
                                description='Approximate number of monthly users')
    screenshot = FileField('Screenshot (optional)', 
        validators=[
            Optional(),
            FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
        ])
    is_open_source = BooleanField('Open Source')
    source_repository = StringField('Source Code Repository', 
        validators=[Optional(), URL()],
        render_kw={"placeholder": "https://github.com/username/repository"})
    submit = SubmitField('Save Changes')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    slug = StringField('Slug')
    description = TextAreaField('Description')
    icon = StringField('Icon Class')
    color = StringField('Color')
    display_order = IntegerField('Display Order', default=0)
    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(max=120, message='Full name must be 120 characters or less')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.lower()).first()
        if user:
            raise ValidationError('Username already taken. Please choose another.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email already registered. Please use another email or login.')

class Setup2FAForm(FlaskForm):
    code = StringField('Verification Code', 
                      validators=[
                          DataRequired(), 
                          Length(min=6, max=6, message='Code must be exactly 6 digits')
                      ],
                      render_kw={"placeholder": "Enter 6-digit code"})
    submit = SubmitField('Verify and Enable 2FA')

class Verify2FAForm(FlaskForm):
    code = StringField('Verification Code',
                      validators=[
                          DataRequired(),
                          Length(min=6, max=6, message='Code must be exactly 6 digits')
                      ],
                      render_kw={"placeholder": "Enter 6-digit code"})
    submit = SubmitField('Verify')

class UseCaseForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    slug = StringField('Slug', validators=[Optional(), Length(max=50)],
                      description='URL-friendly version of name (leave blank to auto-generate)')
    description = TextAreaField('Description', validators=[Optional()])
    icon = StringField('Icon Class', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired(), Length(max=7)])
    display_order = IntegerField('Display Order', default=0)

class IntegrationMethodForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    slug = StringField('Slug', validators=[Optional(), Length(max=50)],
                      description='URL-friendly version of name (leave blank to auto-generate)')
    description = TextAreaField('Description', validators=[Optional()])
    icon = StringField('Icon Class', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired(), Length(max=7)])
    display_order = IntegerField('Display Order', default=0)

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(max=100, message='Name must be 100 characters or less')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    subject = StringField('Subject', validators=[
        DataRequired(),
        Length(max=200, message='Subject must be 200 characters or less')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=10, max=2000, message='Message must be between 10 and 2000 characters')
    ])
    submit = SubmitField('Send Message')

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(max=200, message='Title must be 200 characters or less')
    ])
    slug = StringField('Slug', validators=[
        DataRequired(),
        Length(max=200, message='Slug must be 200 characters or less')
    ])
    category_id = SelectField('Category', 
        coerce=int,
        validators=[DataRequired()]
    )
    excerpt = TextAreaField('Excerpt', validators=[
        Optional(),
        Length(max=500, message='Excerpt must be 500 characters or less')
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(),
        Length(min=10, message='Content must be at least 10 characters')
    ])
    featured_image = FileField('Featured Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    published = BooleanField('Publish')
    featured = BooleanField('Feature')
    submit = SubmitField('Save')

class BlogCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    icon = StringField('Icon Class', validators=[Optional()])
    color = StringField('Color', validators=[Optional()])
    submit = SubmitField('Save')