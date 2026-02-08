#!/usr/bin/env python
"""
Fix PostgreSQL sequences after data migration.
When migrating from SQLite, the auto-increment sequences need to be reset.
"""
import os
import sys
from sqlalchemy import create_engine, text

def fix_sequences(db_url):
    """Reset all PostgreSQL sequences to match the current max IDs."""
    
    engine = create_engine(db_url)
    
    # Tables that have auto-increment primary keys
    tables = [
        'users',
        'patients',
        'cases',
        'case_images',
        'agent_states',
        'agent_outputs',
        'feedback_events',
        'structured_findings',
        'finding_evaluations',
        'ai_test_results'
    ]
    
    with engine.connect() as conn:
        for table in tables:
            try:
                # Start a new transaction for each table
                trans = conn.begin()
                
                # Get the current max ID
                result = conn.execute(text(f"SELECT MAX(id) FROM {table}"))
                max_id = result.scalar()
                
                if max_id is not None:
                    # Reset the sequence to max_id + 1
                    conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), {max_id}, true)"))
                    trans.commit()
                    print(f"✓ {table}: sequence reset to {max_id + 1}")
                else:
                    trans.commit()
                    print(f"✓ {table}: empty table, no sequence reset needed")
                    
            except Exception as e:
                if 'trans' in locals():
                    trans.rollback()
                print(f"⚠ {table}: {str(e)}")
                continue
    
    print("\n" + "="*60)
    print("Sequence reset complete!")
    print("="*60)

if __name__ == '__main__':
    # Get DATABASE_URL from environment
    db_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("ERROR: DATABASE_PUBLIC_URL or DATABASE_URL environment variable not set!")
        print("Run this script with: railway run python fix_sequences.py")
        sys.exit(1)
    
    # Convert postgres:// to postgresql:// if needed
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    print("="*60)
    print("PostgreSQL Sequence Reset")
    print("="*60)
    print()
    
    try:
        fix_sequences(db_url)
    except Exception as e:
        print(f"\n❌ Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
