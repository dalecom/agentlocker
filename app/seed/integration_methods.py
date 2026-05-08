from app import db
from app.models.integration_method import IntegrationMethod

def seed_integration_methods():
    methods = [
        # API Types
        IntegrationMethod(
            name='REST API',
            description='Standard REST API integration for direct data access',
            icon='fas fa-server',
            color='#3B82F6',
            display_order=1
        ),
        IntegrationMethod(
            name='GraphQL API',
            description='Flexible GraphQL API for efficient data querying',
            icon='fas fa-project-diagram',
            color='#E535AB',
            display_order=2
        ),
        IntegrationMethod(
            name='WebSocket API',
            description='Real-time WebSocket integration for live updates',
            icon='fas fa-bolt',
            color='#10B981',
            display_order=3
        ),
        IntegrationMethod(
            name='gRPC API',
            description='High-performance gRPC API integration',
            icon='fas fa-arrows-alt-h',
            color='#244B9B',
            display_order=4
        ),
        IntegrationMethod(
            name='Streaming API',
            description='Streaming API for continuous data flow',
            icon='fas fa-stream',
            color='#8B5CF6',
            display_order=5
        ),

        # Development Tools
        IntegrationMethod(
            name='GitHub Integration',
            description='Direct integration with GitHub workflows',
            icon='fab fa-github',
            color='#333333',
            display_order=6
        ),
        IntegrationMethod(
            name='VS Code Extension',
            description='Visual Studio Code extension integration',
            icon='fas fa-code',
            color='#007ACC',
            display_order=7
        ),
        IntegrationMethod(
            name='Jupyter Notebook',
            description='Jupyter Notebook integration for data science',
            icon='fas fa-book-open',
            color='#F37626',
            display_order=8
        ),
        IntegrationMethod(
            name='Docker Container',
            description='Containerized Docker integration',
            icon='fab fa-docker',
            color='#2496ED',
            display_order=9
        ),
        IntegrationMethod(
            name='Command Line Tool',
            description='CLI tool for terminal-based integration',
            icon='fas fa-terminal',
            color='#4D4D4D',
            display_order=10
        ),

        # SDKs & Libraries
        IntegrationMethod(
            name='Python SDK',
            description='Python software development kit',
            icon='fab fa-python',
            color='#3776AB',
            display_order=11
        ),
        IntegrationMethod(
            name='JavaScript SDK',
            description='JavaScript library and SDK',
            icon='fab fa-js',
            color='#F7DF1E',
            display_order=12
        ),
        IntegrationMethod(
            name='Node.js SDK',
            description='Node.js development kit',
            icon='fab fa-node-js',
            color='#339933',
            display_order=13
        ),
        IntegrationMethod(
            name='Java SDK',
            description='Java development kit and libraries',
            icon='fab fa-java',
            color='#007396',
            display_order=14
        ),
        IntegrationMethod(
            name='Go SDK',
            description='Go language SDK',
            icon='fas fa-code',
            color='#00ADD8',
            display_order=15
        ),

        # Platform Integrations
        IntegrationMethod(
            name='Slack Integration',
            description='Direct Slack workspace integration',
            icon='fab fa-slack',
            color='#4A154B',
            display_order=16
        ),
        IntegrationMethod(
            name='Discord Bot',
            description='Discord bot and server integration',
            icon='fab fa-discord',
            color='#5865F2',
            display_order=17
        ),
        IntegrationMethod(
            name='Microsoft Teams',
            description='Microsoft Teams app integration',
            icon='fas fa-users',
            color='#6264A7',
            display_order=18
        ),
        IntegrationMethod(
            name='Telegram Bot',
            description='Telegram bot integration',
            icon='fab fa-telegram',
            color='#26A5E4',
            display_order=19
        ),
        IntegrationMethod(
            name='WhatsApp Business API',
            description='WhatsApp Business API integration',
            icon='fab fa-whatsapp',
            color='#25D366',
            display_order=20
        ),

        # No-Code Platforms
        IntegrationMethod(
            name='Zapier Integration',
            description='Zapier automation integration',
            icon='fas fa-bolt',
            color='#FF4A00',
            display_order=21
        ),
        IntegrationMethod(
            name='Make.com (Integromat)',
            description='Make.com workflow automation',
            icon='fas fa-cogs',
            color='#14B8A6',
            display_order=22
        ),
        IntegrationMethod(
            name='Bubble.io Plugin',
            description='Bubble.io no-code platform plugin',
            icon='fas fa-circle',
            color='#14B8A6',
            display_order=23
        ),
        IntegrationMethod(
            name='Airtable Extension',
            description='Airtable base extension',
            icon='fas fa-table',
            color='#EF4444',
            display_order=24
        ),
        IntegrationMethod(
            name='Webflow Integration',
            description='Webflow site integration',
            icon='fas fa-w',
            color='#4353FF',
            display_order=25
        ),

        # Cloud Platforms
        IntegrationMethod(
            name='AWS Lambda',
            description='AWS Lambda function integration',
            icon='fab fa-aws',
            color='#FF9900',
            display_order=26
        ),
        IntegrationMethod(
            name='Google Cloud Functions',
            description='Google Cloud Functions integration',
            icon='fab fa-google',
            color='#4285F4',
            display_order=27
        ),
        IntegrationMethod(
            name='Azure Functions',
            description='Microsoft Azure Functions integration',
            icon='fab fa-microsoft',
            color='#0078D4',
            display_order=28
        ),
        IntegrationMethod(
            name='Vercel Integration',
            description='Vercel platform integration',
            icon='fas fa-triangle',
            color='#000000',
            display_order=29
        ),
        IntegrationMethod(
            name='Cloudflare Workers',
            description='Cloudflare Workers integration',
            icon='fas fa-cloud',
            color='#F6821F',
            display_order=30
        ),

        # Development Platforms
        IntegrationMethod(
            name='Android SDK',
            description='Android mobile development kit',
            icon='fab fa-android',
            color='#3DDC84',
            display_order=31
        ),
        IntegrationMethod(
            name='iOS SDK',
            description='iOS mobile development kit',
            icon='fab fa-apple',
            color='#000000',
            display_order=32
        ),
        IntegrationMethod(
            name='Chrome Extension',
            description='Google Chrome browser extension',
            icon='fab fa-chrome',
            color='#4285F4',
            display_order=33
        ),
        IntegrationMethod(
            name='WordPress Plugin',
            description='WordPress CMS plugin',
            icon='fab fa-wordpress',
            color='#21759B',
            display_order=34
        ),
        IntegrationMethod(
            name='Shopify App',
            description='Shopify e-commerce app',
            icon='fab fa-shopify',
            color='#95BF47',
            display_order=35
        ),

        # Enterprise Solutions
        IntegrationMethod(
            name='Enterprise API',
            description='Enterprise-grade API integration',
            icon='fas fa-building',
            color='#3B82F6',
            display_order=36
        ),
        IntegrationMethod(
            name='SaaS Integration',
            description='Software as a Service integration',
            icon='fas fa-cloud',
            color='#8B5CF6',
            display_order=37
        ),
        IntegrationMethod(
            name='SSO Support',
            description='Single Sign-On authentication support',
            icon='fas fa-key',
            color='#10B981',
            display_order=38
        ),
        IntegrationMethod(
            name='API Gateway',
            description='API Gateway integration',
            icon='fas fa-network-wired',
            color='#F97316',
            display_order=39
        ),
        IntegrationMethod(
            name='VPN Access',
            description='Virtual Private Network access',
            icon='fas fa-shield-alt',
            color='#EC4899',
            display_order=40
        ),

        # No Code & Browser
        IntegrationMethod(
            name='Website / Browser',
            description='Direct website or browser integration',
            icon='fas fa-globe',
            color='#3e1ef7',
            display_order=41
        ),
        IntegrationMethod(
            name='No Code',
            description='No-code platform integration',
            icon='fas fa-puzzle-piece',
            color='#F97316',
            display_order=42
        ),

        # Direct Integrations
        IntegrationMethod(
            name='iFrame Embedding',
            description='Embed via iFrame integration',
            icon='fas fa-window-maximize',
            color='#0EA5E9',
            display_order=43
        ),
        IntegrationMethod(
            name='JavaScript Widget',
            description='Embeddable JavaScript widget',
            icon='fas fa-puzzle-piece',
            color='#F7DF1E',
            display_order=44
        ),
        IntegrationMethod(
            name='API Proxy',
            description='API proxy integration',
            icon='fas fa-random',
            color='#3B82F6',
            display_order=45
        ),
        IntegrationMethod(
            name='White Label Solution',
            description='White label integration solution',
            icon='fas fa-tag',
            color='#6B7280',
            display_order=46
        ),
        IntegrationMethod(
            name='Custom Integration',
            description='Custom integration solution',
            icon='fas fa-wrench',
            color='#6B7280',
            display_order=47
        ),
    ]

    # Delete existing methods first
    IntegrationMethod.query.delete()
    
    # Add new methods
    for method in methods:
        db.session.add(method)
    
    try:
        db.session.commit()
        print("Successfully seeded integration methods")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding integration methods: {str(e)}") 