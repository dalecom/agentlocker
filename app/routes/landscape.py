from flask import Blueprint, render_template
from sqlalchemy import func, desc, text
from app.extensions import db
from app.models.agent import Agent
from app.models.category import Category
from app.models.use_case import UseCase
from app.models.integration_method import IntegrationMethod
from app.models.review import Review
import json
from datetime import datetime, timedelta
from collections import defaultdict

landscape_bp = Blueprint('landscape', __name__)

@landscape_bp.route('/ecosystem')
def landscape():
    try:
        # Overall Statistics
        total_agents = Agent.query.filter_by(is_verified=True).count()
        total_reviews = Review.query.count()
        avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0

        # Category Distribution with Sorting and Agents
        categories = Category.query.all()
        category_stats = []
        
        for cat in categories:
            # Get count of agents in this category
            agent_count = Agent.query.filter(
                Agent.categories.contains(cat),
                Agent.is_verified == True
            ).count()
            
            if agent_count > 0:
                # Add to category stats
                category_stats.append({
                    'name': cat.name,
                    'count': agent_count,
                    'percentage': round((agent_count / total_agents) * 100, 1) if total_agents > 0 else 0
                })
                
                # Get all agents for this category
                cat.agents = Agent.query.filter(
                    Agent.categories.contains(cat),
                    Agent.is_verified == True
                ).order_by(
                    desc(Agent.upvote_count)
                ).all()
                
                # Store the count directly on the category object
                setattr(cat, 'agent_count', agent_count)
            else:
                cat.agents = []
                setattr(cat, 'agent_count', 0)

        # Sort categories by count
        categories.sort(key=lambda x: getattr(x, 'agent_count', 0), reverse=True)

        # Filter out categories with no agents
        categories = [cat for cat in categories if getattr(cat, 'agent_count', 0) > 0]

        # Pricing Distribution
        pricing_models = defaultdict(int)
        agents = Agent.query.filter_by(is_verified=True).all()
        for agent in agents:
            try:
                if agent.pricing_info:
                    pricing = json.loads(agent.pricing_info)
                    model = pricing.get('model', 'paid').lower()
                    pricing_models[model] += 1
            except json.JSONDecodeError:
                continue

        # Integration Methods Distribution
        integration_stats = db.session.query(
            IntegrationMethod.name,
            func.count(Agent.id).label('count')
        ).join(
            Agent.integration_method_list
        ).filter(
            Agent.is_verified == True
        ).group_by(
            IntegrationMethod.name
        ).order_by(
            text('count DESC')
        ).all()

        # Growth Trends (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        monthly_growth = db.session.query(
            func.strftime('%Y-%m', Agent.created_at).label('month'),
            func.count(Agent.id).label('count')
        ).filter(
            Agent.created_at >= six_months_ago,
            Agent.is_verified == True
        ).group_by(
            'month'
        ).order_by(
            'month'
        ).all()

        # Ensure we have data for all months
        growth_data = []
        current_date = six_months_ago
        while current_date <= datetime.utcnow():
            month_str = current_date.strftime('%Y-%m')
            month_data = next(
                ((month_str, count) for month, count in monthly_growth if month == month_str),
                (month_str, 0)
            )
            growth_data.append(month_data)
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

        # Open Source Stats
        open_source_count = Agent.query.filter_by(
            is_verified=True,
            is_open_source=True
        ).count()
        
        open_source_percentage = round((open_source_count/total_agents)*100, 1) if total_agents > 0 else 0

        # Use Case Distribution
        use_case_stats = db.session.query(
            UseCase.name,
            func.count(Agent.id).label('count')
        ).join(
            Agent.use_cases
        ).filter(
            Agent.is_verified == True
        ).group_by(
            UseCase.name
        ).order_by(
            text('count DESC')
        ).all()

        # Calculate month-over-month growth
        if len(growth_data) >= 2:
            current_month = growth_data[-1][1]
            previous_month = growth_data[-2][1]
            monthly_growth_rate = round(
                ((current_month - previous_month) / previous_month * 100 if previous_month > 0 else 0), 
                1
            )
        else:
            monthly_growth_rate = 0

        # Get all model objects for icon/color lookup
        use_cases = UseCase.query.all()
        integration_methods = IntegrationMethod.query.all()

        return render_template('landscape.html',
                            total_agents=total_agents,
                            total_reviews=total_reviews,
                            avg_rating=round(avg_rating, 1),
                            category_stats=category_stats,
                            pricing_models=dict(pricing_models),
                            integration_stats=integration_stats,
                            monthly_growth=growth_data,
                            monthly_growth_rate=monthly_growth_rate,
                            open_source_count=open_source_count,
                            open_source_percentage=open_source_percentage,
                            use_case_stats=use_case_stats,
                            categories=categories,
                            use_cases=use_cases,
                            integration_methods=integration_methods)
    
    except Exception as e:
        print(f"Error in landscape route: {str(e)}")  # For debugging
        db.session.rollback()
        return render_template('error.html', error=str(e))