from flask import Flask, request, jsonify
import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    from src.models import DataSource, Patient, LabResult, ClinicalNote
    from src.ingestion import DataIngestion
    from src.storage import CentralizedDataStore
    from src.ai_engine import AIEngine
    from src.services import AlertingService, ClinicalUIService, AnalyticsService
    from src.external import ExternalInterfaces
    
    class HealthcareIntegrationSystem:
        def __init__(self):
            self.ingestion = DataIngestion()
            self.data_store = CentralizedDataStore()
            self.ai_engine = AIEngine()
            self.alerting = AlertingService()
            self.clinical_ui = ClinicalUIService(self.data_store)
            self.analytics = AnalyticsService(self.data_store)
            self.external = ExternalInterfaces()
        
        def process_incoming_data(self, source, raw_data: str, patient_id: str):
            try:
                processed_data = self.ingestion.ingest_data(source, raw_data)
                
                if processed_data['type'] == 'patient':
                    self.data_store.store_patient(processed_data['data'])
                elif processed_data['type'] == 'lab_result':
                    self.data_store.store_lab_result(processed_data['data'], patient_id)
                    alerts = self.ai_engine.analyze_lab_results(processed_data['data'], patient_id)
                    for alert in alerts:
                        self.alerting.send_alert(patient_id, alert, "high")
                elif processed_data['type'] == 'clinical_note':
                    self.data_store.store_clinical_note(processed_data['data'], patient_id)
                    alerts = self.ai_engine.analyze_clinical_notes(processed_data['data'], patient_id)
                    for alert in alerts:
                        self.alerting.send_alert(patient_id, alert, "medium")
                
                return f"✅ Data from {source.value} processed successfully"
                
            except Exception as e:
                return f"❌ Error: {str(e)}"
    
    system = HealthcareIntegrationSystem()
    print("✅ Healthcare system loaded successfully!")
    
except Exception as e:
    print(f"❌ Error loading system: {e}")
    # Create dummy system for demo
    class HealthcareIntegrationSystem:
        def __init__(self):
            self.data_store = type('obj', (object,), {
                'get_patient_data': lambda x: {'patient': None, 'lab_results': [], 'clinical_notes': []},
                'patients': {},
                'lab_results': [],
                'clinical_notes': []
            })
            self.analytics = type('obj', (object,), {
                'get_statistics': lambda: {'total_patients': 0, 'total_lab_results': 0, 'total_notes': 0}
            })
            self.alerting = type('obj', (object,), {'active_alerts': []})
            self.external = type('obj', (object,), {
                'generate_nhif_billing': lambda x, y: {'status': 'demo'}
            })
    
    system = HealthcareIntegrationSystem()
    print("⚠️ Using demo mode")

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏥 Advanced Healthcare System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .card { background: #f9f9f9; padding: 20px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007cba; }
            .alert { color: #d63384; font-weight: bold; }
            .success { color: #198754; }
            .form-group { margin: 15px 0; }
            input, select, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .nav { background: #343a40; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .nav a { color: white; text-decoration: none; margin: 0 15px; padding: 10px; }
            .nav a:hover { background: #495057; border-radius: 3px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
            .stat-card { background: #e7f3ff; padding: 20px; text-align: center; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <a href="/">🏠 Home</a>
                <a href="/add-data">➕ Add Data</a>
                <a href="/patients">👥 Patients</a>
                <a href="/analytics">📊 Analytics</a>
                <a href="/api">🔌 API</a>
            </div>
            
            <h1>🏥 Advanced Healthcare Integration System</h1>
            <p>Welcome to your complete healthcare data management platform!</p>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>👥 Patients</h3>
                    <p style="font-size: 24px; font-weight: bold;">""" + str(len(system.data_store.patients)) + """</p>
                </div>
                <div class="stat-card">
                    <h3>🔬 Lab Results</h3>
                    <p style="font-size: 24px; font-weight: bold;">""" + str(len(system.data_store.lab_results)) + """</p>
                </div>
                <div class="stat-card">
                    <h3>📝 Clinical Notes</h3>
                    <p style="font-size: 24px; font-weight: bold;">""" + str(len(system.data_store.clinical_notes)) + """</p>
                </div>
                <div class="stat-card">
                    <h3>🚨 Active Alerts</h3>
                    <p style="font-size: 24px; font-weight: bold;">""" + str(len(system.alerting.active_alerts)) + """</p>
                </div>
            </div>
            
            <div class="card">
                <h2>Quick Actions</h2>
                <p><a href="/add-data"><button>➕ Add New Patient Data</button></a></p>
                <p><a href="/patients"><button>👥 View All Patients</button></a></p>
                <p><a href="/analytics"><button>📊 System Analytics</button></a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/add-data', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        try:
            patient_id = request.form['patient_id']
            data_type = request.form['data_type']
            raw_data = request.form['raw_data']
            
            source_map = {'ehr': DataSource.EHR, 'lis': DataSource.LIS, 'phr': DataSource.PHR}
            source = source_map[data_type]
            
            result = system.process_incoming_data(source, raw_data, patient_id)
            
            return f"""
            <div class="container">
                <div class="nav"><a href="/">Home</a> <a href="/add-data">Add More Data</a></div>
                <div class="card success">
                    <h2>✅ Data Processed Successfully!</h2>
                    <p>{result}</p>
                    <p><strong>Patient ID:</strong> {patient_id}</p>
                    <p><strong>Data Type:</strong> {data_type.upper()}</p>
                    <p><a href="/patient/{patient_id}">View Patient Record</a></p>
                </div>
            </div>
            """
        except Exception as e:
            return f"""
            <div class="container">
                <div class="nav"><a href="/">Home</a></div>
                <div class="card alert">
                    <h2>❌ Error Processing Data</h2>
                    <p>Error: {str(e)}</p>
                </div>
            </div>
            """
    
    return """
    <div class="container">
        <div class="nav"><a href="/">Home</a></div>
        <h2>➕ Add Patient Data</h2>
        
        <form method="post" class="card">
            <div class="form-group">
                <label><strong>Patient ID:</strong></label>
                <input type="text" name="patient_id" value="P001" required>
            </div>
            
            <div class="form-group">
                <label><strong>Data Type:</strong></label>
                <select name="data_type" required>
                    <option value="ehr">📋 EHR Patient Information</option>
                    <option value="lis">🔬 Lab Results (HL7)</option>
                    <option value="phr">👤 Patient Symptoms (PHR)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label><strong>Data Content:</strong></label>
                <textarea name="raw_data" rows="8" placeholder="Paste your JSON or HL7 data here..." required></textarea>
            </div>
            
            <button type="submit">Process Data</button>
        </form>
        
        <div class="card">
            <h3>📋 Sample Data Formats</h3>
            
            <h4>EHR Patient Data (JSON):</h4>
            <textarea rows="4" readonly>{"patient_id": "P002", "name": "Jane Smith", "birthDate": "1990-05-20", "gender": "female"}</textarea>
            
            <h4>Lab Results (HL7):</h4>
            <textarea rows="4" readonly>MSH|^~\&|LIS|HOSP|EHR|HOSP|202312011200||ORU^R01|123|P|2.3|PID|||P001||Doe^John||19800115|M|||123 Main St^^Anytown^NY^12345||(555)123-4567|||M|||123-45-6789|OBR|1|12345^LIS|98765^GLUCOSE|||202312011000|||||||||12345^Doctor^Adam|||||||||202312011200|OBX|1|SN|2345-7^GLUCOSE^LN||215|mg/dL|70-110|H|||F</textarea>
            
            <h4>Patient Symptoms (JSON):</h4>
            <textarea rows="3" readonly>{"symptoms": "fever and cough for 3 days", "timestamp": "2023-12-01T14:30:00Z"}</textarea>
        </div>
    </div>
    """

@app.route('/patients')
def list_patients():
    patients = system.data_store.patients
    html = """
    <div class="container">
        <div class="nav"><a href="/">Home</a> <a href="/add-data">Add Data</a></div>
        <h2>👥 Patient Registry</h2>
        <p>Total Patients: """ + str(len(patients)) + """</p>
    """
    
    if patients:
        for patient_id, patient in patients.items():
            patient_data = system.data_store.get_patient_data(patient_id)
            html += f"""
            <div class="card">
                <h3>👤 {patient.name} (ID: {patient_id})</h3>
                <p>📅 DOB: {patient.dob} | ⚧ Gender: {patient.gender}</p>
                <p>🔬 Lab Results: {len(patient_data.get('lab_results', []))} | 📝 Notes: {len(patient_data.get('clinical_notes', []))}</p>
                <p><a href="/patient/{patient_id}">View Full Record</a></p>
            </div>
            """
    else:
        html += "<p>No patients found. <a href='/add-data'>Add some data</a> to get started.</p>"
    
    html += "</div>"
    return html

@app.route('/patient/<patient_id>')
def view_patient(patient_id):
    data = system.data_store.get_patient_data(patient_id)
    
    html = f"""
    <div class="container">
        <div class="nav"><a href="/">Home</a> <a href="/patients">All Patients</a></div>
        <h1>👤 Patient Record: {patient_id}</h1>
    """
    
    if data.get('patient'):
        patient = data['patient']
        html += f"""
        <div class="card">
            <h2>📋 Patient Information</h2>
            <p><strong>Name:</strong> {patient.name}</p>
            <p><strong>Date of Birth:</strong> {patient.dob}</p>
            <p><strong>Gender:</strong> {patient.gender}</p>
        </div>
        """
    else:
        html += "<p>No patient information found.</p>"
    
    # Lab Results
    html += f"""
    <div class="card">
        <h2>🔬 Lab Results ({len(data.get('lab_results', []))})</h2>
    """
    
    if data.get('lab_results'):
        for lab in data['lab_results']:
            html += f"""
            <div style="margin: 10px 0; padding: 15px; background: #e8f5e8; border-radius: 5px;">
                <strong>🧪 {lab.test_name}:</strong> {lab.result} {lab.units}
                <br><small>📊 Normal range: {lab.normal_range} | ⏰ {lab.timestamp}</small>
            </div>
            """
    else:
        html += "<p>No lab results available.</p>"
    html += "</div>"
    
    # Clinical Notes
    html += f"""
    <div class="card">
        <h2>📝 Clinical Notes ({len(data.get('clinical_notes', []))})</h2>
    """
    
    if data.get('clinical_notes'):
        for note in data['clinical_notes']:
            html += f"""
            <div style="margin: 10px 0; padding: 15px; background: #e3f2fd; border-radius: 5px;">
                <strong>📋 {note.note_type}:</strong> {note.content}
                <br><small>👤 Author: {note.author} | ⏰ {note.timestamp}</small>
            </div>
            """
    else:
        html += "<p>No clinical notes available.</p>"
    html += "</div>"
    
    html += "</div>"
    return html

@app.route('/analytics')
def analytics():
    stats = system.analytics.get_statistics()
    
    html = """
    <div class="container">
        <div class="nav"><a href="/">Home</a></div>
        <h1>📊 System Analytics Dashboard</h1>
        
        <div class="stats">
            <div class="stat-card">
                <h3>👥 Total Patients</h3>
                <p style="font-size: 32px; font-weight: bold;">""" + str(stats.get('total_patients', 0)) + """</p>
            </div>
            <div class="stat-card">
                <h3>🔬 Lab Results</h3>
                <p style="font-size: 32px; font-weight: bold;">""" + str(stats.get('total_lab_results', 0)) + """</p>
            </div>
            <div class="stat-card">
                <h3>📝 Clinical Notes</h3>
                <p style="font-size: 32px; font-weight: bold;">""" + str(stats.get('total_notes', 0)) + """</p>
            </div>
        </div>
        
        <div class="card">
            <h2>🚨 Active Alerts</h2>
    """
    
    if system.alerting.active_alerts:
        for alert in system.alerting.active_alerts:
            html += f"""
            <div style="color: #d63384; font-weight: bold; padding: 10px; background: #fff3f3; margin: 5px 0; border-radius: 3px;">
                🚨 [{alert['priority'].upper()}] Patient {alert['patient_id']}: {alert['message']}
            </div>
            """
    else:
        html += "<p>✅ No active alerts. System is running normally.</p>"
    
    html += """
        </div>
        
        <div class="card">
            <h2>💡 System Information</h2>
            <p>🏥 Healthcare Integration System v1.0</p>
            <p>📅 System Status: <span style="color: green;">🟢 Operational</span></p>
            <p>🔧 Features: Data Ingestion, AI Analysis, Alerting, Analytics</p>
        </div>
    </div>
    """
    
    return html

@app.route('/api')
def api_docs():
    return """
    <div class="container">
        <div class="nav"><a href="/">Home</a></div>
        <h1>🔌 API Documentation</h1>
        
        <div class="card">
            <h2>REST API Endpoints</h2>
            <p>Your system is ready for API integration!</p>
            
            <h3>📋 Available Endpoints:</h3>
            <ul>
                <li><code>GET /api/patients</code> - List all patients</li>
                <li><code>GET /api/patient/&lt;id&gt;</code> - Get patient data</li>
                <li><code>POST /api/data</code> - Submit new data</li>
                <li><code>GET /api/analytics</code> - System statistics</li>
            </ul>
            
            <h3>🔮 Next Steps for Deployment:</h3>
            <ul>
                <li>Add database persistence (SQLite/PostgreSQL)</li>
                <li>Implement user authentication</li>
                <li>Add HTTPS security</li>
                <li>Deploy to cloud (AWS/Azure/Heroku)</li>
                <li>Connect to real EHR systems</li>
            </ul>
        </div>
    </div>
    """

# REST API Endpoints
@app.route('/api/patients', methods=['GET'])
def api_patients():
    patients = list(system.data_store.patients.keys())
    return jsonify({'patients': patients, 'count': len(patients)})

@app.route('/api/patient/<patient_id>', methods=['GET'])
def api_patient(patient_id):
    data = system.data_store.get_patient_data(patient_id)
    return jsonify(data)

@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    stats = system.analytics.get_statistics()
    return jsonify(stats)

if __name__ == '__main__':
    print("🚀 STARTING ADVANCED HEALTHCARE SYSTEM WEB INTERFACE...")
    print("📍 Local URL: http://localhost:5000")
    print("📊 Features: Web UI, REST API, Analytics Dashboard")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)