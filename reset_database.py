# reset_database.py - Fixed import error
from muranga_dashboard import app, db
from src.database import Patient, ANCVisit, Alert
from muranga_dashboard import User  # Import User from the main app
from datetime import datetime

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Recreate all tables with new schema
        db.create_all()
        
        print("✅ Database tables created successfully!")
        
        # Recreate default users
        from muranga_dashboard import create_default_users
        create_default_users()
        
        # Add a sample patient to test the new schema
        try:
            sample_patient = Patient(
                patient_id="MUR001",
                name="Test Patient",
                dob=datetime(1990, 5, 15).date(),
                gestation_weeks=24,
                phone="0720123456",
                village="Murang'a Town",
                registered_date=datetime.utcnow()
            )
            db.session.add(sample_patient)
            db.session.commit()
            print("✅ Sample patient added with phone and village fields!")
        except Exception as e:
            print(f"⚠️ Could not add sample patient: {e}")
            db.session.rollback()

if __name__ == '__main__':
    reset_database()
    print("✅ Database reset completed!")