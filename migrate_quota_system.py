#!/usr/bin/env python3
"""
Database migration script to add quota system tables.
Run this script once to add the CashFlow and QuotaHistory tables to the database.
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.models import db, CashFlow, QuotaHistory, Wallet

def migrate_database():
    """Add quota system tables to the database"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Fix postgres:// to postgresql:// if needed
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    # Check if tables already exist
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")
    
    with engine.connect() as conn:
        # Add quota columns to wallets table if they don't exist
        if 'wallets' in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('wallets')]
            
            if 'initial_quota_value' not in columns:
                print("Adding initial_quota_value column to wallets table...")
                conn.execute(text(
                    "ALTER TABLE wallets ADD COLUMN initial_quota_value FLOAT DEFAULT 1.0 NOT NULL"
                ))
                conn.commit()
                print("✓ Added initial_quota_value column")
            else:
                print("✓ initial_quota_value column already exists")
            
            if 'current_quota_quantity' not in columns:
                print("Adding current_quota_quantity column to wallets table...")
                conn.execute(text(
                    "ALTER TABLE wallets ADD COLUMN current_quota_quantity FLOAT DEFAULT 0.0 NOT NULL"
                ))
                conn.commit()
                print("✓ Added current_quota_quantity column")
            else:
                print("✓ current_quota_quantity column already exists")
        
        # Create cash_flows table if it doesn't exist
        if 'cash_flows' not in existing_tables:
            print("Creating cash_flows table...")
            conn.execute(text("""
                CREATE TABLE cash_flows (
                    id SERIAL PRIMARY KEY,
                    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    type VARCHAR(10) NOT NULL,
                    amount FLOAT NOT NULL,
                    description TEXT,
                    quota_value_at_time FLOAT NOT NULL,
                    quotas_issued FLOAT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✓ Created cash_flows table")
        else:
            print("✓ cash_flows table already exists")
        
        # Create quota_history table if it doesn't exist
        if 'quota_history' not in existing_tables:
            print("Creating quota_history table...")
            conn.execute(text("""
                CREATE TABLE quota_history (
                    id SERIAL PRIMARY KEY,
                    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    quota_value FLOAT NOT NULL,
                    quota_quantity FLOAT NOT NULL,
                    networth FLOAT NOT NULL
                )
            """))
            conn.commit()
            print("✓ Created quota_history table")
        else:
            print("✓ quota_history table already exists")
    
    print("\n✅ Database migration completed successfully!")
    print("\nQuota system is now ready to use.")
    print("You can start tracking cash flows and quota performance for each wallet.")

if __name__ == '__main__':
    migrate_database()

