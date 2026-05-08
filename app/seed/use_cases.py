from app import db
from app.models.use_case import UseCase

def seed_use_cases():
    use_cases = [
        UseCase(
            name='Text Generation',
            description='Generate human-like text and content',
            icon='fas fa-pen-fancy',
            color='#3B82F6',
            display_order=1
        ),
        UseCase(
            name='Image Generation',
            description='Create, edit and manipulate images',
            icon='fas fa-image',
            color='#8B5CF6',
            display_order=2
        ),
        UseCase(
            name='Code Assistant',
            description='Help with coding and development tasks',
            icon='fas fa-code',
            color='#10B981',
            display_order=3
        ),
        UseCase(
            name='Data Analysis',
            description='Analyze and visualize data',
            icon='fas fa-chart-bar',
            color='#F59E0B',
            display_order=4
        ),
        UseCase(
            name='Audio/Speech',
            description='Process and generate audio content',
            icon='fas fa-microphone-alt',
            color='#EF4444',
            display_order=5
        ),
        UseCase(
            name='Video Creation',
            description='Create and edit video content',
            icon='fas fa-video',
            color='#EC4899',
            display_order=6
        ),
        UseCase(
            name='Research & Analysis',
            description='Assist with research and data analysis',
            icon='fas fa-search',
            color='#6366F1',
            display_order=7
        ),
        UseCase(
            name='SEO & Content',
            description='Optimize content for search engines',
            icon='fas fa-chart-line',
            color='#14B8A6',
            display_order=8
        ),
        UseCase(
            name='Design & Graphics',
            description='Create and edit graphic designs',
            icon='fas fa-palette',
            color='#8B5CF6',
            display_order=9
        ),
        UseCase(
            name='Customer Support',
            description='Provide customer service and support',
            icon='fas fa-headset',
            color='#06B6D4',
            display_order=10
        ),
        UseCase(
            name='Task Automation',
            description='Automate repetitive tasks and workflows',
            icon='fas fa-cogs',
            color='#10B981',
            display_order=11
        ),
    ]

    # Delete existing use cases first
    UseCase.query.delete()
    
    # Add new use cases
    for use_case in use_cases:
        db.session.add(use_case)
    
    try:
        db.session.commit()
        print("Successfully seeded use cases")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding use cases: {str(e)}") 