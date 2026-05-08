from app import create_app, db
from app.models import Agent  # Import all your models here
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Create all tables fresh
    db.create_all()
    
    # Clear alembic_version table if it exists
    db.session.execute(text('DROP TABLE IF EXISTS alembic_version'))
    db.session.commit()
    
    # Print tables created
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables created:", tables)