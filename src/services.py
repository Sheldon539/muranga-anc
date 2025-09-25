from datetime import datetime
# No changes needed here unless there are other imports

class AlertingService:
    def __init__(self):
        self.active_alerts = []
    
    def send_alert(self, patient_id: str, message: str, priority: str = "medium"):
        alert = {
            'patient_id': patient_id,
            'message': message,
            'priority': priority,
            'timestamp': datetime.now(),
            'acknowledged': False
        }
        self.active_alerts.append(alert)
        print(f"ALERT [{priority.upper()}]: Patient {patient_id} - {message}")

class ClinicalUIService:
    def __init__(self, data_store):
        self.data_store = data_store
    
    def display_patient_summary(self, patient_id: str):
        data = self.data_store.get_patient_data(patient_id)
        print(f"\n=== Patient Summary ===")
        if data['patient']:
            print(f"Name: {data['patient'].name}")
            print(f"DOB: {data['patient'].dob}")
        print(f"Lab Results: {len(data['lab_results'])}")
        print(f"Clinical Notes: {len(data['clinical_notes'])}")

class AnalyticsService:
    def __init__(self, data_store):
        self.data_store = data_store
    
    def get_statistics(self):
        stats = {
            'total_patients': len(self.data_store.patients),
            'total_lab_results': len(self.data_store.lab_results),
            'total_notes': len(self.data_store.clinical_notes)
        }
        return stats