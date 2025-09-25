# muranga_dashboard.py
from flask import Flask, request
import json
import sys
import os

sys.path.append(os.path.dirname(__file__))

try:
    from src.muranga_adapter import MurangaANCAdapter
    from src.hypertension_ai import PregnancyRiskLevel
    print("✅ Murang'a County AI system loaded successfully!")
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Make sure all files are in the correct locations")
    exit(1)

app = Flask(__name__)
adapter = MurangaANCAdapter()

MURANGA_CLINICS = [
    "Murang'a County Hospital", "Kangema Sub-County Hospital", 
    "Maragua Hospital", "Kiharu Health Centre", "Gatanga Health Centre"
]

@app.route('/')
def muranga_dashboard():
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏥 Murang'a County - Hypertension in Pregnancy AI System</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f8ff; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 10px; }}
            .clinic-card {{ background: white; margin: 15px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .risk-low {{ border-left: 5px solid #27ae60; }}
            .risk-moderate {{ border-left: 5px solid #f39c12; }}
            .risk-high {{ border-left: 5px solid #e74c3c; }}
            .risk-critical {{ border-left: 5px solid #c0392b; background: #ffebee; }}
            .alert-critical {{ background: #ffcccc; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            button {{ background: #3498db; color: white; padding: 15px; border: none; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #2980b9; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏥 Murang'a County ANC AI System</h1>
            <p>Hypertension in Pregnancy Detection & Management</p>
            <p>📍 Murang'a County Health Facilities</p>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
            <div class="clinic-card">
                <h3>📊 Quick Statistics</h3>
                <p>👥 ANC Patients Today: <strong>47</strong></p>
                <p>🚨 High Risk Cases: <strong>8</strong></p>
                <p>✅ Normal Assessments: <strong>39</strong></p>
            </div>

            <div class="clinic-card">
                <h3>⚡ Quick Assessment</h3>
                <a href="/assess"><button style="width: 100%; font-size: 16px;">➕ New Patient Assessment</button></a>
            </div>
        </div>

        <div class="clinic-card">
            <h3>🏥 Participating Health Facilities</h3>
            <ul>
                {"".join([f"<li>{clinic}</li>" for clinic in MURANGA_CLINICS])}
            </ul>
        </div>

        <div class="clinic-card">
            <h3>🎯 Research Objectives</h3>
            <p>This system supports research on AI-based detection of hypertensive disorders in pregnancy in Murang'a County ANC clinics.</p>
            <p><strong>Target:</strong> 300 pregnant women + 30 nurses</p>
            <p><strong>Goal:</strong> Reduce maternal mortality from HDPs</p>
            <p><strong>Alignment:</strong> Kenya UHC & Digital Health Strategy 2020-2030</p>
        </div>

        <div class="clinic-card">
            <h3>🔍 How It Works</h3>
            <p>1. Nurse enters patient data (BP, urinalysis, symptoms)</p>
            <p>2. AI analyzes risk factors using evidence-based rules</p>
            <p>3. System provides immediate risk assessment</p>
            <p>4. High-risk cases get urgent alerts for referral</p>
        </div>
    </body>
    </html>
    '''

@app.route('/assess', methods=['GET', 'POST'])
def assess_patient():
    if request.method == 'POST':
        # Process ANC data
        patient_data = {
            'patient_id': request.form['patient_id'],
            'name': request.form['name'],
            'dob': request.form['dob'],
            'gestation_weeks': int(request.form['gestation_weeks']),
            'systolic_bp': int(request.form['systolic_bp']),
            'diastolic_bp': int(request.form['diastolic_bp']),
            'urine_protein': int(request.form['urine_protein']),
            'symptoms': request.form.getlist('symptoms'),
            'medical_history': request.form.getlist('medical_history')
        }
        
        result = adapter.process_anc_data(json.dumps(patient_data))
        
        if 'error' not in result:
            risk = result['risk_assessment']
            
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
                <div class="alert-critical">
                    <h3>🚨 CRITICAL ALERT</h3>
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
                    .alert-critical {{ background: #ffcccc; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h1>📋 ANC Assessment Result</h1>
                <a href="/">← Back to Dashboard</a>
                
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
                    <h3>👤 Patient Information</h3>
                    <p><strong>Name:</strong> {patient_data['name']}</p>
                    <p><strong>Gestation:</strong> {patient_data['gestation_weeks']} weeks</p>
                    <p><strong>BP:</strong> {patient_data['systolic_bp']}/{patient_data['diastolic_bp']} mmHg</p>
                    <p><strong>Urine Protein:</strong> +{patient_data['urine_protein']}</p>
                    <p><strong>Symptoms:</strong> {", ".join(patient_data['symptoms']) if patient_data['symptoms'] else "None"}</p>
                    <p><strong>Medical History:</strong> {", ".join(patient_data['medical_history']) if patient_data['medical_history'] else "None"}</p>
                </div>

                <div class="risk-card">
                    <h3>📝 Clinical Actions</h3>
                    <p>1. Document this assessment in patient records</p>
                    <p>2. Follow the recommended action plan</p>
                    <p>3. Schedule follow-up as indicated</p>
                    <p>4. For critical cases: initiate immediate referral</p>
                </div>
            </body>
            </html>
            '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>New Assessment</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f8ff; }
            .form-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            input, select {{ width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }}
            .form-group {{ margin: 15px 0; }}
            button {{ background: #27ae60; color: white; padding: 15px; border: none; border-radius: 5px; width: 100%; cursor: pointer; }}
            button:hover {{ background: #219a52; }}
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>➕ New ANC Patient Assessment</h1>
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
                    <label><input type="checkbox" name="medical_history" value="multiple_pregnancy"> Multiple Pregnancy</label>
                </div>
                
                <button type="submit">🔍 Assess Hypertension Risk</button>
            </form>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🏥 MURANG'A COUNTY ANC AI SYSTEM")
    print("📍 Specialized for Hypertension in Pregnancy Detection")
    print("📋 Based on Concept Note: 'AI for HDP Detection in Murang'a County'")
    print("🌐 Dashboard: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*60)
    app.run(debug=True, port=5001)