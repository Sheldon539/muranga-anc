# muranga_dashboard.py - ENHANCED WITH DATABASE
from flask import Flask, request, jsonify
import json
import sys
import os
from datetime import datetime

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

# Initialize Database
init_db(app)
adapter = MurangaANCAdapter()

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

@app.route('/')
def muranga_dashboard():
    stats = get_patient_stats()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏥 Murang'a County - AI System (DATABASE ENABLED)</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f8ff; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 10px; }}
            .clinic-card {{ background: white; margin: 15px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #e7f3ff; padding: 20px; text-align: center; border-radius: 5px; }}
            .database-badge {{ background: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏥 Murang'a County ANC AI System <span class="database-badge">DATABASE ENABLED</span></h1>
            <p>Hypertension in Pregnancy Detection & Management</p>
            <p>📍 Murang'a County Health Facilities | 💾 Data Persistence: ACTIVE</p>
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
            <div class="clinic-card">
                <h3>⚡ Quick Actions</h3>
                <a href="/assess"><button style="background: #3498db; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; font-size: 16px; margin: 5px 0;">➕ New Patient Assessment</button></a>
                <a href="/patients"><button style="background: #2ecc71; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; font-size: 16px; margin: 5px 0;">👥 View All Patients</button></a>
                <a href="/alerts"><button style="background: #e74c3c; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; font-size: 16px; margin: 5px 0;">🚨 Active Alerts</button></a>
            </div>

            <div class="clinic-card">
                <h3>💾 Database Status</h3>
                <p>✅ SQLite Database: <strong>ACTIVE</strong></p>
                <p>✅ Data Persistence: <strong>ENABLED</strong></p>
                <p>✅ Patient Records: <strong>SAVED</strong></p>
                <p>✅ Visit History: <strong>TRACKED</strong></p>
                <p>🔍 File: <code>muranga_health.db</code></p>
            </div>
        </div>

        <div class="clinic-card">
            <h3>🏥 Participating Health Facilities</h3>
            <ul>
                {"".join([f"<li>{clinic}</li>" for clinic in MURANGA_CLINICS])}
            </ul>
        </div>
    </body>
    </html>
    '''

@app.route('/assess', methods=['GET', 'POST'])
def assess_patient():
    if request.method == 'POST':
        try:
            # Get form data
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
                'visit_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Process with AI
            result = adapter.process_anc_data(json.dumps(patient_data))
            
            if 'error' not in result:
                risk = result['risk_assessment']
                
                # SAVE TO DATABASE
                with app.app_context():
                    # Save or update patient
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
                    
                    # Save visit
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
                    
                    # Save alert if high risk
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
                
                # Determine risk color
                if risk['risk_level'] == PregnancyRiskLevel.LOW:
                    risk_color = '#27ae60'
                    risk_class = 'risk-low'
                elif risk['risk_level'] == PregnancyRiskLevel.MODERATE:
                    risk_color = '#f39c12'
                    risk_class = 'risk-moderate'
                elif risk['risk_level'] == PregnancyRiskLevel.HIGH:
                    risk_color = '#e74c3c'
                    risk_class = 'risk-high'
                else:
                    risk_color = '#c0392b'
                    risk_class = 'risk-critical'
                
                alert_html = ""
                if result['alert']:
                    alert_html = f'''
                    <div style="background: #ffcccc; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3>🚨 CRITICAL ALERT - SAVED TO DATABASE</h3>
                        <p><strong>Priority:</strong> {result['alert']['priority']}</p>
                        <p><strong>Action Needed:</strong> {risk['recommendation']}</p>
                        <p><strong>Risk Factors:</strong> {", ".join(risk['risk_factors'])}</p>
                    </div>
                    '''
                
                return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Assessment Result</title>
                    <style>
                        body {{ font-family: Arial; margin: 20px; background: #f0f8ff; }}
                        .risk-card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                        .risk-low {{ border-left: 5px solid #27ae60; }}
                        .risk-moderate {{ border-left: 5px solid #f39c12; }}
                        .risk-high {{ border-left: 5px solid #e74c3c; }}
                        .risk-critical {{ border-left: 5px solid #c0392b; background: #ffebee; }}
                        .database-success {{ background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                    </style>
                </head>
                <body>
                    <h1>📋 ANC Assessment Result <span style="background: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px;">SAVED TO DATABASE</span></h1>
                    <a href="/">← Back to Dashboard</a>
                    
                    <div class="database-success">
                        <strong>✅ SUCCESS:</strong> Patient data saved to database. Visit recorded and alert stored.
                    </div>
                    
                    {alert_html}
                    
                    <div class="risk-card {risk_class}">
                        <h2>Risk Assessment: {risk['risk_level'].value}</h2>
                        <p><strong>Risk Score:</strong> {risk['risk_score']}/10</p>
                        <p><strong>Recommendation:</strong> {risk['recommendation']}</p>
                    </div>

                    <div class="risk-card">
                        <h3>📊 Risk Factors Identified</h3>
                        <ul>
                            {"".join([f"<li>{factor}</li>" for factor in risk['risk_factors']])}
                        </ul>
                    </div>

                    <div class="risk-card">
                        <h3>👤 Patient Information (SAVED)</h3>
                        <p><strong>Patient ID:</strong> {patient_data['patient_id']}</p>
                        <p><strong>Name:</strong> {patient_data['name']}</p>
                        <p><strong>Gestation:</strong> {patient_data['gestation_weeks']} weeks</p>
                        <p><strong>BP:</strong> {patient_data['systolic_bp']}/{patient_data['diastolic_bp']} mmHg</p>
                        <p><strong>Urine Protein:</strong> +{patient_data['urine_protein']}</p>
                    </div>
                </body>
                </html>
                '''
            else:
                return f"Error: {result['error']}"
                
        except Exception as e:
            return f"Error processing data: {str(e)}"
    
    # GET request - show form
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>New Assessment</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f8ff; }
            .form-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            input, select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
            .form-group { margin: 15px 0; }
            button { background: #27ae60; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; cursor: pointer; }
            a { color: #3498db; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>➕ New ANC Patient Assessment <span style="background: #3498db; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px;">DATABASE ENABLED</span></h1>
        <a href="/">← Back to Dashboard</a>
        
        <div class="form-card">
            <form method="post">
                <div class="form-group">
                    <h3>👤 Patient Details</h3>
                    <input type="text" name="patient_id" placeholder="Patient ID (e.g., MUR001)" required>
                    <input type="text" name="name" placeholder="Full Name" required>
                    <input type="date" name="dob" placeholder="Date of Birth" required>
                </div>
                
                <div class="form-group">
                    <h3>🤰 Pregnancy Details</h3>
                    <input type="number" name="gestation_weeks" placeholder="Gestational Age (weeks)" min="12" max="42" required>
                </div>
                
                <div class="form-group">
                    <h3>💓 Vital Signs</h3>
                    <input type="number" name="systolic_bp" placeholder="Systolic BP" min="60" max="250" required>
                    <input type="number" name="diastolic_bp" placeholder="Diastolic BP" min="40" max="150" required>
                </div>
                
                <div class="form-group">
                    <h3>🧪 Urinalysis</h3>
                    <select name="urine_protein" required>
                        <option value="0">Protein: Negative (0)</option>
                        <option value="1">Protein: Trace (+1)</option>
                        <option value="2">Protein: +2</option>
                        <option value="3">Protein: +3 or more</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <h3>🚨 Symptoms (Check all that apply)</h3>
                    <label><input type="checkbox" name="symptoms" value="severe headache"> Severe Headache</label><br>
                    <label><input type="checkbox" name="symptoms" value="visual disturbances"> Visual Disturbances</label><br>
                    <label><input type="checkbox" name="symptoms" value="epigastric pain"> Epigastric Pain</label><br>
                    <label><input type="checkbox" name="symptoms" value="swelling"> Severe Swelling</label>
                </div>
                
                <div class="form-group">
                    <h3>📋 Medical History (Check all that apply)</h3>
                    <label><input type="checkbox" name="medical_history" value="previous_preeclampsia"> Previous Preeclampsia</label><br>
                    <label><input type="checkbox" name="medical_history" value="chronic_hypertension"> Chronic Hypertension</label><br>
                    <label><input type="checkbox" name="medical_history" value="diabetes"> Diabetes</label><br>
                    <label><input type="checkbox" name="medical_history" value="first_pregnancy"> First Pregnancy</label>
                </div>
                
                <button type="submit">💾 Save Assessment to Database</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/patients')
def list_patients():
    with app.app_context():
        patients = Patient.query.all()
        
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Patient Registry</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f8ff; }
            .patient-card { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <h1>👥 Patient Registry <span style="background: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px;">DATABASE</span></h1>
        <a href="/">← Back to Dashboard</a>
        <p>Total Patients: ''' + str(len(patients)) + '''</p>
    '''
    
    for patient in patients:
        html += f'''
        <div class="patient-card">
            <h3>👤 {patient.name} (ID: {patient.patient_id})</h3>
            <p>📅 DOB: {patient.dob} | 🤰 Gestation: {patient.gestation_weeks} weeks</p>
            <p>📅 Registered: {patient.created_at.strftime('%Y-%m-%d')}</p>
        </div>
        '''
    
    html += '</body></html>'
    return html

@app.route('/alerts')
def list_alerts():
    with app.app_context():
        alerts = Alert.query.order_by(Alert.created_at.desc()).all()
        
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Active Alerts</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f8ff; }
            .alert-card { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .critical { border-left: 5px solid #e74c3c; background: #ffebee; }
            .high { border-left: 5px solid #f39c12; background: #fff3e0; }
        </style>
    </head>
    <body>
        <h1>🚨 Active Alerts <span style="background: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px;">DATABASE</span></h1>
        <a href="/">← Back to Dashboard</a>
        <p>Total Alerts: ''' + str(len(alerts)) + '''</p>
    '''
    
    for alert in alerts:
        alert_class = 'critical' if alert.priority == 'CRITICAL' else 'high'
        html += f'''
        <div class="alert-card {alert_class}">
            <h3>🚨 {alert.priority} ALERT - Patient {alert.patient_id}</h3>
            <p><strong>Message:</strong> {alert.message}</p>
            <p><strong>Risk Score:</strong> {alert.risk_score}</p>
            <p><strong>Time:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        '''
    
    html += '</body></html>'
    return html

if __name__ == '__main__':
    print("🏥 MURANG'A COUNTY ANC AI SYSTEM - DATABASE ENABLED")
    print("💾 SQLite Database: muranga_health.db")
    print("🌐 Dashboard: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*60)
    app.run(debug=True, port=5001)