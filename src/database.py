# src/database.py - Updated with complete Patient model
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)  # Changed from age to dob
    gender = db.Column(db.String(10), default='female')
    gestation_weeks = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(15))  # Added phone field
    village = db.Column(db.String(100))  # Added village field
    registered_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with visits
    visits = db.relationship('ANCVisit', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.patient_id}: {self.name}>'

class ANCVisit(db.Model):
    __tablename__ = 'anc_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), db.ForeignKey('patients.patient_id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    gestation_weeks = db.Column(db.Integer, nullable=False)
    systolic_bp = db.Column(db.Integer, nullable=False)
    diastolic_bp = db.Column(db.Integer, nullable=False)
    urine_protein = db.Column(db.Integer, nullable=False)
    symptoms = db.Column(db.Text)  # JSON string of symptoms
    medical_history = db.Column(db.Text)  # JSON string of medical history
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<ANCVisit {self.patient_id} - {self.visit_date}>'

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), db.ForeignKey('patients.patient_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = db.Column(db.Float, nullable=False)
    risk_factors = db.Column(db.Text)  # JSON string of risk factors
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Alert {self.patient_id} - {self.priority}>'

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///muranga_anc.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("✅ Database initialized successfully!")