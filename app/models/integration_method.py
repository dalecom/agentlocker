from app.extensions import db
from datetime import datetime

# Define the association table first
agent_integration_methods = db.Table('agent_integration_methods',
    db.Column('agent_id', db.Integer, db.ForeignKey('agent.id', ondelete='CASCADE'), primary_key=True),
    db.Column('integration_method_id', db.Integer, db.ForeignKey('integration_method.id', ondelete='CASCADE'), primary_key=True)
)

class IntegrationMethod(db.Model):
    __tablename__ = 'integration_method'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationship with agents through association table
    agents = db.relationship('Agent', 
                           secondary=agent_integration_methods,
                           lazy='dynamic', 
                           back_populates='integration_method_list')