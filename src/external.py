from datetime import datetime
# No changes needed here unless there are other imports

class ExternalInterfaces:
    @staticmethod
    def generate_nhif_billing(patient_id: str, services: list) -> dict:
        return {
            'patient_id': patient_id,
            'services': services,
            'billing_date': datetime.now().isoformat(),
            'status': 'generated'
        }
    
    @staticmethod
    def export_public_health_data(patient_data: dict) -> bool:
        print(f"Exporting anonymized data for public health registry")
        return True