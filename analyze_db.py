from app import create_app, db
from sqlalchemy import inspect, text
from app.models.agent import Agent
from app.models.category import Category
from app.models.user import User
from app.models.role import Role
from app.models.review import Review
from app.models.use_case import UseCase
from app.models.integration_method import IntegrationMethod
from pprint import pprint
from datetime import datetime

def analyze_database():
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("\n=== DATABASE ANALYSIS REPORT ===")
        print(f"Generated at: {datetime.now()}\n")
        
        # Get all table names
        tables = inspector.get_table_names()
        print(f"Total Tables: {len(tables)}")
        print("Tables:", ", ".join(tables))
        
        # Analyze each table
        for table_name in tables:
            print(f"\n=== TABLE: {table_name} ===")
            
            # Get columns
            columns = inspector.get_columns(table_name)
            print("\nColumns:")
            for col in columns:
                print(f"- {col['name']}: {col['type']} (nullable: {col['nullable']})")
            
            # Get primary keys
            pks = inspector.get_pk_constraint(table_name)
            print(f"\nPrimary Keys: {', '.join(pks['constrained_columns'])}")
            
            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print("\nForeign Keys:")
                for fk in fks:
                    print(f"- {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print("\nIndexes:")
                for idx in indexes:
                    print(f"- {idx['name']}: {', '.join(idx['column_names'])} (unique: {idx['unique']})")
            
            # Get row count - Fixed query
            row_count = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            print(f"\nRow Count: {row_count}")

        # Print some basic statistics
        print("\n=== STATISTICS ===")
        stats = {
            'Total Users': User.query.count(),
            'Total Agents': Agent.query.count(),
            'Verified Agents': Agent.query.filter_by(is_verified=True).count(),
            'Total Categories': Category.query.count(),
            'Total Reviews': Review.query.count(),
            'Total Use Cases': UseCase.query.count(),
            'Total Integration Methods': IntegrationMethod.query.count(),
        }
        
        for key, value in stats.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    analyze_database()