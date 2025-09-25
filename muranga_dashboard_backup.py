# muranga_dashboard.py - WITH USER AUTHENTICATION
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import sys
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.append(os.path.dirname(__file__))

try:
    from src.muranga_adapter import MurangaANCAdapter
    from src.hypertension_ai import PregnancyRiskLevel
    from src.database import db, Patient, ANCVisit, Alert, init_db
    print("✅ All modules loaded successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

app = Flask(__name__)
app.secret_key = 'muranga-health-secret-key-2024'  # Important for sessions

# Initialize Database
init_db(app)
adapter = MurangaANCAdapter()

# Authentication Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the system.'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    facility = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create default users
with app.app_context():
    db.create_all()  # Ensure all tables exist
    
    if not User.query.filter_by(username='nurse1').first():
        nurse = User(
            username='nurse1',
            role='nurse', 
            full_name='Jane Mwende',
            facility="Murang'a County Hospital"
        )
        nurse.set_password('nurse123')
        db.session.add(nurse)
    
    if not User.query.filter_by(username='doctor1').first():
        doctor = User(
            username='doctor1',
            role='doctor',
            full_name='Dr. Kamau Waweru', 
            facility="Murang'a County Hospital"
        )
        doctor.set_password('doctor123')
        db.session.add(doctor)
    
    db.session.commit()

MURANGA_CLINICS = [
    "Murang'a County Hospital", "Kangema Sub-County Hospital", 
    "Maragua Hospital", "Kiharu Health Centre", "Gatanga Health Centre"
]

def get_patient_stats():
    """Get statistics from database"""
    with app.app_context():
        total_patients = Patient.query.count()
        total_visits = ANCVisit.query.count()
        total_alerts = Alert.query.count()
        critical_alerts = Alert.query.filter_by(priority='CRITICAL').count()
        
        return {
            'total_patients': total_patients,
            'total_visits': total_visits,
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('muranga_dashboard'))
        else:
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>Login Failed</title></head>
            <body style="font-family: Arial; margin: 50px;">
                <h2>❌ Login Failed</h2>
                <p>Invalid username or password.</p>
                <a href="/login">Try Again</a>
            </body>
            </html>
            '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Murang'a County - Login</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; background: #f0f8ff; }
            .login-container { max-width: 400px; margin: 100px auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #3498db; color: white; padding: 12px; border: none; border-radius: 5px; width: 100%; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>🏥 Murang'a County ANC System</h2>
            <p>Please log in to continue</p>
            
            <form method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <h4>Demo Accounts:</h4>
                <p><strong>Nurse:</strong> nurse1 / nurse123</p>
                <p><strong>Doctor:</strong> doctor1 / doctor123</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def muranga_dashboard():
    stats = get_patient_stats()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏥 Murang'a County - AI System (AUTHENTICATED)</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f8ff; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 10px; }}
            .user-info {{ background: #34495e; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #e7f3ff; padding: 20px; text-align: center; border-radius: 5px; }}
            .badge {{ background: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }}
            .auth-badge {{ background: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1>🏥 Murang'a County ANC AI System <span class="badge">AUTHENTICATED</span></h1>
                    <p>Hypertension in Pregnancy Detection & Management</p>
                </div>
                <div style="text-align: right;">
                    <div class="user-info">
                        <strong>👤 {current_user.full_name}</strong><br>
                        <small>Role: {current_user.role} | Facility: {current_user.facility}</small>
                    </div>
                    <a href="/logout" style="color: white; text-decoration: none;">🚪 Logout</a>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>👥 Total Patients</h3>
                <p style="font-size: 24px; font-weight: bold;">{stats['total_patients']}</p>
            </div>
            <div class="stat-card">
                <h3>📋 ANC Visits</h3>
                <p style="font-size: 24px; font-weight: bold;">{stats['total_visits']}</p>
            </div>
            <div class="stat-card">
                <h3>🚨 Alerts</h3>
                <p style="font-size: 24px; font-weight: bold;">{stats['total_alerts']}</p>
            </div>
            <div class="stat-card">
                <h3>⚠️ Critical</h3>
                <p style="font-size: 24px; font-weight: bold;">{stats['critical_alerts']}</p>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>⚡ Quick Actions</h3>
                <a href="/assess"><button style="background: #3498db; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; font-size: 16px; margin: 5px 0;">➕ New Patient Assessment</button></a>
                <a href="/patients"><button style="background: #2ecc71; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; font-size: 16px; margin: 5px 0;">👥 View All Patients</button></a>
                <a href="/alerts"><button style="background: #e74c3c; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; font-size: 16px; margin: 5px 0;">🚨 Active Alerts</button></a>
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>🔐 System Status</h3>
                <p>✅ Authentication: <strong>ACTIVE</strong> <span class="auth-badge">LOGGED IN</span></p>
                <p>✅ User: <strong>{current_user.full_name}</strong></p>
                <p>✅ Role: <strong>{current_user.role.upper()}</strong></p>
                <p>✅ Facility: <strong>{current_user.facility}</strong></p>
                <p>💾 Database: <strong>ACTIVE</strong></p>
            </div>
        </div>

        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin: 20px 0;">
            <h3>🏥 Participating Health Facilities</h3>
            <ul>
                {"".join([f"<li>{clinic}</li>" for clinic in MURANGA_CLINICS])}
            </ul>
        </div>
    </body>
    </html>
    '''

@app.route('/assess', methods=['GET', 'POST'])
@login_required
def assess_patient():
    if request.method == 'POST':
        try:
            patient_data = {
                'patient_id': request.form['patient_id'],
                'name': request.form['name'],
                'dob': request.form['dob'],
                'gestation_weeks': int(request.form['gestation_weeks']),
                'systolic_bp': int(request.form['systolic_bp']),
                'diastolic_bp': int(request.form['diastolic_bp']),
                'urine_protein': int(request.form['urine_protein']),
                'symptoms': request.form.getlist('symptoms'),
                'medical_history': request.form.getlist('medical_history'),
                'visit_date': datetime.now().strftime('%Y-%m-%d'),
                'assessed_by': current_user.full_name
            }
            
            result = adapter.process_anc_data(json.dumps(patient_data))
            
            if 'error' not in result:
                risk = result['risk_assessment']
                
                with app.app_context():
                    patient = Patient.query.filter_by(patient_id=patient_data['patient_id']).first()
                    if not patient:
                        patient = Patient(
                            patient_id=patient_data['patient_id'],
                            name=patient_data['name'],
                            dob=patient_data['dob'],
                            gender='female',
                            gestation_weeks=patient_data['gestation_weeks']
                        )
                        db.session.add(patient)
                    
                    visit = ANCVisit(
                        patient_id=patient_data['patient_id'],
                        visit_date=patient_data['visit_date'],
                        gestation_weeks=patient_data['gestation_weeks'],
                        systolic_bp=patient_data['systolic_bp'],
                        diastolic_bp=patient_data['diastolic_bp'],
                        urine_protein=patient_data['urine_protein'],
                        symptoms=json.dumps(patient_data['symptoms']),
                        medical_history=json.dumps(patient_data['medical_history']),
                        risk_score=risk['risk_score'],
                        risk_level=risk['risk_level'].value,
                        recommendation=risk['recommendation']
                    )
                    db.session.add(visit)
                    
                    if result['alert']:
                        alert = Alert(
                            patient_id=patient_data['patient_id'],
                            message=result['alert']['message'],
                            priority=result['alert']['priority'],
                            risk_score=risk['risk_score'],
                            risk_factors=json.dumps(risk['risk_factors'])
                        )
                        db.session.add(alert)
                    
                    db.session.commit()
                
                if risk['risk_level'] == PregnancyRiskLevel.LOW:
                    risk_class = 'risk-low'
                elif risk['risk_level'] == PregnancyRiskLevel.MODERATE:
                    risk_class = 'risk-moderate'
                elif risk['risk_level'] == PregnancyRiskLevel.HIGH:
                    risk_class = 'risk-high'
                else:
                    risk_class = 'risk-critical'
                
                alert_html = ""
                if result['alert']:
                    alert_html = f'''
                    <div style="background: #ffcccc; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3>🚨 CRITICAL ALERT</h3>
                        <p><strong>Priority:</strong> {result['alert']['priority']}</p>
                        <p><strong>Action Needed:</strong> {risk['recommendation']}</p>
                    </div>
                    '''
                
                return f'''
                <!DOCTYPE html>
                <html>
                <head><title>Assessment Result</title>
                <style>
                    body {{ font-family: Arial; margin: 20px; background: #f0f8ff; }}
                    .risk-card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .risk-low {{ border-left: 5px solid #27ae60; }}
                    .risk-moderate {{ border-left: 5px solid #f39c12; }}
                    .risk-high {{ border-left: 5px solid #e74c3c; }}
                    .risk-critical {{ border-left: 5px solid #c0392b; background: #ffebee; }}
                </style>
                </head>
                <body>
                    <h1>📋 Assessment Result <span class="badge">ASSESSED BY: {current_user.full_name}</span></h1>
                    <a href="/">← Dashboard</a>
                    
                    {alert_html}
                    
                    <div class="risk-card {risk_class}">
                        <h2>Risk: {risk['risk_level'].value}</h2>
                        <p><strong>Score:</strong> {risk['risk_score']}/10</p>
                        <p><strong>Recommendation:</strong> {risk['recommendation']}</p>
                    </div>
                </body>
                </html>
                '''
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>New Assessment</title>
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f0f8ff; }}
        .form-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        input, select {{ width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }}
    </style>
    </head>
    <body>
        <h1>➕ New Assessment <small>(Assessing as: {current_user.full_name})</small></h1>
        <a href="/">← Dashboard</a>
        
        <div class="form-card">
            <form method="post">
                <h3>👤 Patient Details</h3>
                <input type="text" name="patient_id" placeholder="Patient ID" required>
                <input type="text" name="name" placeholder="Full Name" required>
                <input type="date" name="dob" required>
                
                <h3>🤰 Pregnancy</h3>
                <input type="number" name="gestation_weeks" placeholder="Weeks" min="12" max="42" required>
                
                <h3>💓 Vital Signs</h3>
                <input type="number" name="systolic_bp" placeholder="Systolic BP" required>
                <input type="number" name="diastolic_bp" placeholder="Diastolic BP" required>
                
                <h3>🧪 Urinalysis</h3>
                <select name="urine_protein" required>
                    <option value="0">Protein: Negative</option>
                    <option value="1">Protein: +1</option>
                    <option value="2">Protein: +2</option>
                    <option value="3">Protein: +3</option>
                </select>
                
                <h3>🚨 Symptoms</h3>
                <label><input type="checkbox" name="symptoms" value="headache"> Headache</label>
                <label><input type="checkbox" name="symptoms" value="visual"> Visual Issues</label>
                
                <h3>📋 History</h3>
                <label><input type="checkbox" name="medical_history" value="previous_preeclampsia"> Previous Preeclampsia</label>
                <label><input type="checkbox" name="medical_history" value="hypertension"> Hypertension</label>
                
                <br><button type="submit" style="background: #27ae60; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%;">💾 Save Assessment</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/patients')
@login_required
def list_patients():
    with app.app_context():
        patients = Patient.query.all()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Patients</title></head>
    <body style="font-family: Arial; margin: 20px;">
        <h1>👥 Patients</h1>
        <a href="/">← Dashboard</a>
        <p>Total: {len(patients)}</p>
        {"".join([f"<div style='background: white; padding: 10px; margin: 5px 0;'><strong>{p.name}</strong> (ID: {p.patient_id})</div>" for p in patients])}
    </body>
    </html>
    '''

@app.route('/alerts')
@login_required
def list_alerts():
    with app.app_context():
        alerts = Alert.query.all()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Alerts</title></head>
    <body style="font-family: Arial; margin: 20px;">
        <h1>🚨 Alerts</h1>
        <a href="/">← Dashboard</a>
        <p>Total: {len(alerts)}</p>
        {"".join([f"<div style='background: #ffebee; padding: 10px; margin: 5px 0;'><strong>{a.priority}</strong>: {a.message}</div>" for a in alerts])}
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🏥 MURANG'A COUNTY ANC AI SYSTEM - AUTHENTICATION ENABLED")
    print("🔐 Login Required: http://localhost:5001")
    print("👤 Demo Nurse: nurse1 / nurse123")
    print("👨‍⚕️ Demo Doctor: doctor1 / doctor123")
    print("🛑 Press Ctrl+C to stop")
    print("="*60)
    app.run(debug=True, port=5001)