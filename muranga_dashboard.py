# muranga_dashboard.py - WITH COMPLETE UPDATES
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import sys
import os
from datetime import datetime, timedelta, date
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
app.secret_key = 'muranga-health-secret-key-2024'

# Initialize Database FIRST
init_db(app)

# THEN create adapter after app is configured
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

def create_default_users():
    with app.app_context():
        db.create_all()
        
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
        print("✅ Default users created successfully!")

create_default_users()

MURANGA_CLINICS = [
    "Murang'a County Hospital", "Kangema Sub-County Hospital", 
    "Maragua Hospital", "Kiharu Health Centre", "Gatanga Health Centre"
]

def generate_patient_id():
    last_patient = Patient.query.order_by(Patient.id.desc()).first()
    if last_patient:
        last_id = int(last_patient.patient_id.replace('MUR', ''))
        new_id = f"MUR{last_id + 1:03d}"
    else:
        new_id = "MUR001"
    return new_id

def get_patient_stats():
    try:
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
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {'total_patients': 0, 'total_visits': 0, 'total_alerts': 0, 'critical_alerts': 0}

def get_recent_patients():
    try:
        recent_visits = ANCVisit.query.order_by(ANCVisit.visit_date.desc()).limit(5).all()
        recent_patients = []
        
        for visit in recent_visits:
            patient = Patient.query.filter_by(patient_id=visit.patient_id).first()
            if patient:
                if visit.risk_level == 'LOW':
                    status = 'normal'
                elif visit.risk_level == 'MODERATE':
                    status = 'warning'
                else:
                    status = 'critical'
                
                recent_patients.append({
                    'name': patient.name,
                    'id': patient.patient_id,
                    'visit_date': visit.visit_date,
                    'bp_systolic': visit.systolic_bp,
                    'bp_diastolic': visit.diastolic_bp,
                    'status': status
                })
        
        if not recent_patients:
            recent_patients = [
                {'name': 'Mary Kariuki', 'id': 'MUR009', 'visit_date': '24/Sep/2025', 
                 'bp_systolic': 120, 'bp_diastolic': 80, 'status': 'normal'},
            ]
        
        return recent_patients
    except Exception as e:
        print(f"Error getting recent patients: {e}")
        return [
            {'name': 'Mary Kariuki', 'id': 'MUR009', 'visit_date': '24/Sep/2025', 
             'bp_systolic': 120, 'bp_diastolic': 80, 'status': 'normal'},
        ]

def create_test_alerts():
    """Create sample alerts for testing if none exist"""
    with app.app_context():
        try:
            # Check if we have any alerts
            existing_alerts = Alert.query.count()
            if existing_alerts > 0:
                return  # Don't create test alerts if we already have some
            
            # Check if we have any patients
            patients = Patient.query.limit(3).all()
            
            if not patients:
                print("No patients found. Creating test patients first...")
                # Create test patients
                test_patients = [
                    Patient(patient_id="MUR001", name="Mary Wanjiku", dob=date(1990, 5, 15), 
                           gestation_weeks=28, phone="0712345678", village="Kangema"),
                    Patient(patient_id="MUR002", name="Grace Nyambura", dob=date(1985, 8, 22), 
                           gestation_weeks=32, phone="0723456789", village="Maragua"),
                    Patient(patient_id="MUR003", name="Esther Wairimu", dob=date(1995, 3, 10), 
                           gestation_weeks=25, phone="0734567890", village="Kiharu")
                ]
                for patient in test_patients:
                    db.session.add(patient)
                db.session.commit()
                patients = test_patients
            
            # Create test alerts
            test_alerts = [
                Alert(patient_id=patients[0].patient_id, 
                     message="Critical blood pressure reading: 160/110 mmHg", 
                     priority="CRITICAL", risk_score=9.5,
                     risk_factors=json.dumps(["Hypertension", "Proteinuria"]),
                     created_at=datetime.now()),
                Alert(patient_id=patients[1].patient_id, 
                     message="Moderate risk: Elevated blood pressure with symptoms", 
                     priority="HIGH", risk_score=7.2,
                     risk_factors=json.dumps(["Headache", "Visual disturbances"]),
                     created_at=datetime.now() - timedelta(hours=2)),
                Alert(patient_id=patients[2].patient_id, 
                     message="Monitor for pre-eclampsia symptoms", 
                     priority="MEDIUM", risk_score=5.8,
                     risk_factors=json.dumps(["First pregnancy", "Family history"]),
                     created_at=datetime.now() - timedelta(days=1))
            ]
            
            for alert in test_alerts:
                db.session.add(alert)
            
            db.session.commit()
            print("✅ Test alerts created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating test alerts: {e}")
            db.session.rollback()

# Create test alerts on startup
create_test_alerts()

@app.route('/error/<error>')
def handle_errors(error):
    return render_template('error.html', error=error)

@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(RecursionError)
def handle_http_errors(e):
    error_message = ""
    status_code = 500
    
    if isinstance(e, RecursionError):
        error_message = "System error: Maximum recursion depth exceeded."
        status_code = 500
    elif hasattr(e, 'code') and e.code == 404:
        error_message = "Page not found."
        status_code = 404
    else:
        error_message = "Internal server error."
        status_code = 500
    
    try:
        return render_template('error.html', error_message=error_message), status_code
    except:
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error - Murang'a ANC System</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container">
                <div class="error-container mx-auto text-center">
                    <div class="error-icon">⚠️</div>
                    <h1 class="text-danger">System Error</h1>
                    <div class="card shadow-sm">
                        <div class="card-body">
                            <p class="lead">{error_message}</p>
                            <a href="/" class="btn btn-primary me-2">Return to Dashboard</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """, status_code

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['user_name'] = user.full_name
            session['user_role'] = user.role
            session['facility'] = user.facility
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    try:
        stats = get_patient_stats()
        recent_patients = get_recent_patients()
        
        return render_template('dashboard.html',
                             total_patients=stats['total_patients'],
                             anc_visits=stats['total_visits'],
                             alerts=stats['total_alerts'],
                             critical=stats['critical_alerts'],
                             recent_patients=recent_patients,
                             muranga_clinics=MURANGA_CLINICS)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('error.html', error=f"Dashboard error: {str(e)}"), 500

@app.route('/add-patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        try:
            patient_id = generate_patient_id()
            name = request.form['name']
            dob_str = request.form['dob']
            gestation_weeks = int(request.form['gestation_weeks'])
            phone = request.form.get('phone', '')
            village = request.form.get('village', '')
            
            # Convert string date to Python date object
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
                return redirect(url_for('add_patient'))
            
            new_patient = Patient(
                patient_id=patient_id,
                name=name,
                dob=dob,
                gestation_weeks=gestation_weeks,
                phone=phone,
                village=village,
                registered_date=datetime.utcnow()
            )
            
            db.session.add(new_patient)
            db.session.commit()
            
            flash(f'Patient {name} added successfully with ID: {patient_id}', 'success')
            return redirect(url_for('list_patients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding patient: {str(e)}', 'error')
            return redirect(url_for('add_patient'))
    
    return render_template('add_patient.html')

@app.route('/assess', methods=['GET', 'POST'])
@login_required
def assess_patient():
    if request.method == 'POST':
        try:
            # Extract form data
            patient_data = {
                'patient_id': request.form['patient_id'],
                'name': request.form['name'],
                'dob': request.form['dob'],  # This is a string
                'gestation_weeks': int(request.form['gestation_weeks']),
                'systolic_bp': int(request.form['systolic_bp']),
                'diastolic_bp': int(request.form['diastolic_bp']),
                'urine_protein': int(request.form['urine_protein']),
                'symptoms': request.form.getlist('symptoms'),
                'medical_history': request.form.getlist('medical_history'),
                'visit_date': datetime.now().strftime('%Y-%m-%d'),
                'assessed_by': current_user.full_name
            }
            
            # Process assessment through adapter
            result = adapter.process_anc_data(json.dumps(patient_data))
            
            if 'error' not in result:
                risk = result['risk_assessment']
                
                # Convert dob string to date object
                try:
                    dob_date = datetime.strptime(patient_data['dob'], '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
                    return redirect(url_for('assess_patient'))
                
                # Check if patient exists, create if not
                patient = Patient.query.filter_by(patient_id=patient_data['patient_id']).first()
                if not patient:
                    patient = Patient(
                        patient_id=patient_data['patient_id'],
                        name=patient_data['name'],
                        dob=dob_date,  # Use the converted date object
                        gender='female',
                        gestation_weeks=patient_data['gestation_weeks'],
                        phone='',  # Provide default values
                        village=''
                    )
                    db.session.add(patient)
                    db.session.flush()  # Get the patient ID without committing
                
                # Create the visit record with proper datetime object
                visit = ANCVisit(
                    patient_id=patient_data['patient_id'],
                    visit_date=datetime.now(),  # Use datetime object
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
                
                # Create alert if needed
                if result.get('alert'):
                    alert = Alert(
                        patient_id=patient_data['patient_id'],
                        message=result['alert']['message'],
                        priority=result['alert']['priority'],
                        risk_score=risk['risk_score'],
                        risk_factors=json.dumps(risk['risk_factors']),
                        created_at=datetime.now()
                    )
                    db.session.add(alert)
                
                # Commit all changes
                db.session.commit()
                
                # Return assessment result
                return render_template('assessment_result.html',
                                     risk=risk,
                                     result=result,
                                     patient_data=patient_data)
            else:
                flash(f"Assessment error: {result['error']}", 'error')
                return redirect(url_for('assess_patient'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error during assessment: {str(e)}', 'error')
            return redirect(url_for('assess_patient'))
    
    # GET request - show assessment form
    return render_template('assessment_form.html')

@app.route('/patients')
@login_required
def list_patients():
    try:
        patients = Patient.query.all()
        return render_template('patients.html', patients=patients)
    except Exception as e:
        flash(f'Error loading patients: {str(e)}', 'error')
        return render_template('patients.html', patients=[])

@app.route('/patient/<patient_id>')
@login_required
def patient_profile(patient_id):
    try:
        patient = Patient.query.filter_by(patient_id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('list_patients'))
        
        visits = ANCVisit.query.filter_by(patient_id=patient_id).order_by(ANCVisit.visit_date.desc()).all()
        
        return render_template('patient_profile.html', 
                             patient=patient, 
                             visits=visits)
    except Exception as e:
        flash(f'Error loading patient profile: {str(e)}', 'error')
        return redirect(url_for('list_patients'))

@app.route('/alerts')
@login_required
def list_alerts():
    try:
        alerts = Alert.query.order_by(Alert.created_at.desc()).all()
        
        # Get patient information for each alert
        patient_map = {}
        for alert in alerts:
            patient = Patient.query.filter_by(patient_id=alert.patient_id).first()
            if patient:
                patient_map[alert.patient_id] = patient
        
        # Count alerts by priority
        critical_count = len([a for a in alerts if a.priority == 'CRITICAL'])
        high_count = len([a for a in alerts if a.priority == 'HIGH'])
        medium_count = len([a for a in alerts if a.priority == 'MEDIUM'])
        
        return render_template('alerts.html', 
                             alerts=alerts,
                             patient_map=patient_map,
                             critical_count=critical_count,
                             high_count=high_count,
                             medium_count=medium_count)
    except Exception as e:
        flash(f'Error loading alerts: {str(e)}', 'error')
        # Return empty data on error
        return render_template('alerts.html', 
                             alerts=[],
                             patient_map={},
                             critical_count=0,
                             high_count=0,
                             medium_count=0)

@app.route('/reports')
@login_required
def reports():
    try:
        # Basic statistics
        stats = get_patient_stats()
        
        # Patient demographics
        patients = Patient.query.all()
        total_patients = len(patients)
        
        # Age distribution - handle missing attributes gracefully
        age_groups = {'<20': 0, '20-25': 0, '26-30': 0, '31-35': 0, '>35': 0}
        for patient in patients:
            # Calculate age from date of birth if available
            if hasattr(patient, 'dob') and patient.dob:
                try:
                    # Parse the dob string or use the date object
                    if isinstance(patient.dob, str):
                        dob_date = datetime.strptime(patient.dob, '%Y-%m-%d')
                    else:
                        dob_date = patient.dob
                    
                    today = datetime.now()
                    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                    
                    if age < 20:
                        age_groups['<20'] += 1
                    elif 20 <= age <= 25:
                        age_groups['20-25'] += 1
                    elif 26 <= age <= 30:
                        age_groups['26-30'] += 1
                    elif 31 <= age <= 35:
                        age_groups['31-35'] += 1
                    else:
                        age_groups['>35'] += 1
                except:
                    # If age calculation fails, skip this patient for age distribution
                    pass
        
        # Gestation distribution - handle missing gestation_weeks
        gestation_groups = {'1st trimester (<14w)': 0, '2nd trimester (14-27w)': 0, '3rd trimester (28w+)': 0}
        for patient in patients:
            if hasattr(patient, 'gestation_weeks') and patient.gestation_weeks is not None:
                if patient.gestation_weeks < 14:
                    gestation_groups['1st trimester (<14w)'] += 1
                elif 14 <= patient.gestation_weeks <= 27:
                    gestation_groups['2nd trimester (14-27w)'] += 1
                else:
                    gestation_groups['3rd trimester (28w+)'] += 1
        
        # Risk level distribution from visits
        visits = ANCVisit.query.all()
        risk_distribution = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0}
        for visit in visits:
            risk_level = visit.risk_level
            if risk_level in risk_distribution:
                risk_distribution[risk_level] += 1
        
        # Monthly visit trends (last 6 months)
        monthly_visits = {}
        for i in range(5, -1, -1):
            month = (datetime.now() - timedelta(days=30*i)).strftime('%Y-%m')
            monthly_visits[month] = 0
        
        for visit in visits:
            visit_month = visit.visit_date.strftime('%Y-%m') if isinstance(visit.visit_date, datetime) else visit.visit_date[:7]
            if visit_month in monthly_visits:
                monthly_visits[visit_month] += 1
        
        # Location distribution - handle missing village/address fields
        locations = {}
        for patient in patients:
            # Try different possible location attributes
            location = 'Unknown'
            if hasattr(patient, 'village') and patient.village:
                location = patient.village
            elif hasattr(patient, 'address') and patient.address:
                location = patient.address
            elif hasattr(patient, 'location') and patient.location:
                location = patient.location
            
            locations[location] = locations.get(location, 0) + 1
        
        return render_template('reports.html',
                             stats=stats,
                             total_patients=total_patients,
                             age_groups=age_groups,
                             gestation_groups=gestation_groups,
                             risk_distribution=risk_distribution,
                             monthly_visits=monthly_visits,
                             villages=locations,  # Use locations instead of villages
                             visits_count=len(visits))
    
    except Exception as e:
        flash(f'Error generating reports: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/template-fallback')
def template_fallback():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Template Missing</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="alert alert-warning">
                <h4>Template Configuration Required</h4>
                <p>The requested template is missing.</p>
                <a href="/" class="btn btn-primary">Return to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)