# Simple main.py that imports everything directly
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now import using absolute paths
try:
    from src.models import DataSource
    from src.ingestion import DataIngestion
    from src.storage import CentralizedDataStore
    from src.ai_engine import AIEngine
    from src.services import AlertingService, ClinicalUIService, AnalyticsService
except ImportError:
    # If absolute imports fail, try relative imports
    from .models import DataSource
    from .ingestion import DataIngestion
    from .storage import CentralizedDataStore
    from .ai_engine import AIEngine
    from .services import AlertingService, ClinicalUIService, AnalyticsService

class HealthcareIntegrationSystem:
    def __init__(self):
        self.ingestion = DataIngestion()
        self.data_store = CentralizedDataStore()
        self.ai_engine = AIEngine()
        self.alerting = AlertingService()
        self.clinical_ui = ClinicalUIService(self.data_store)
        self.analytics = AnalyticsService(self.data_store)
    
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
            
            print(f"✅ Data from {source.value} processed successfully")
            
        except Exception as e:
            print(f"❌ Error processing data: {e}")

if __name__ == "__main__":
    system = HealthcareIntegrationSystem()
    
    ehr_data = '{"patient_id": "P001", "name": "John Doe", "birthDate": "1980-01-15", "gender": "male"}'
    lis_data = "MSH|^~\\&|LIS|HOSP|EHR|HOSP|202312011200||ORU^R01|123|P|2.3|PID|||P001||Doe^John||19800115|M|||123 Main St^^Anytown^NY^12345||(555)123-4567|||M|||123-45-6789|OBR|1|12345^LIS|98765^GLUCOSE|||202312011000|||||||||12345^Doctor^Adam|||||||||202312011200|OBX|1|SN|2345-7^GLUCOSE^LN||215|mg/dL|70-110|H|||F"
    phr_data = '{"symptoms": "patient reports chest pain and shortness of breath", "timestamp": "2023-12-01T12:00:00Z"}'
    
    system.process_incoming_data(DataSource.EHR, ehr_data, "P001")
    system.process_incoming_data(DataSource.LIS, lis_data, "P001")
    system.process_incoming_data(DataSource.PHR, phr_data, "P001")
    
    system.clinical_ui.display_patient_summary("P001")
    
    stats = system.analytics.get_statistics()
    print(f"\n=== System Analytics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")