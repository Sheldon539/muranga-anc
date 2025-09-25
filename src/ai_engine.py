class AIEngine:
    def __init__(self):
        self.alerts = []
    
    def analyze_lab_results(self, lab_result, patient_id: str) -> list:
        alerts = []
        
        if "glucose" in lab_result.test_name.lower():
            try:
                glucose_value = float(lab_result.result)
                if glucose_value > 180:
                    alerts.append(f"High glucose alert: {glucose_value} mg/dL")
                elif glucose_value < 70:
                    alerts.append(f"Low glucose alert: {glucose_value} mg/dL")
            except ValueError:
                pass
        
        return alerts
    
    def analyze_clinical_notes(self, note, patient_id: str) -> list:
        alerts = []
        critical_keywords = ['chest pain', 'shortness of breath', 'fever']
        
        for keyword in critical_keywords:
            if keyword in note.content.lower():
                alerts.append(f"Critical symptom mentioned: {keyword}")
        
        return alerts