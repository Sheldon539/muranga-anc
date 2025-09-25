# src/muranga_adapter.py
import json
from .models import PregnancyPatient, ANCVisit
from .hypertension_ai import HypertensionAIAnalyzer

class MurangaANCAdapter:
    def __init__(self):
        self.ai_analyzer = HypertensionAIAnalyzer()
    
    def process_anc_data(self, raw_data: str) -> dict:
        """Process ANC data from Murang'a County clinics"""
        try:
            data = json.loads(raw_data)
            
            # Create pregnancy patient
            patient = PregnancyPatient(
                data.get('patient_id'),
                data.get('name'),
                data.get('dob'),
                data.get('gender', 'female'),
                data.get('gestation_weeks', 0)
            )
            
            # Create ANC visit
            visit = ANCVisit(
                data.get('visit_date', '2024-01-01'),
                data.get('gestation_weeks', 0)
            )
            
            visit.systolic_bp = data.get('systolic_bp')
            visit.diastolic_bp = data.get('diastolic_bp')
            visit.urine_protein = data.get('urine_protein', 0)
            visit.symptoms = data.get('symptoms', [])
            
            # AI Risk Assessment
            risk_data = {
                'systolic_bp': visit.systolic_bp,
                'diastolic_bp': visit.diastolic_bp,
                'gestational_age_weeks': visit.gestation_weeks,
                'urine_protein': visit.urine_protein,
                'symptoms': visit.symptoms,
                'medical_history': data.get('medical_history', [])
            }
            
            risk_assessment = self.ai_analyzer.analyze_pregnancy_hypertension_risk(risk_data)
            visit.risk_assessment = risk_assessment
            
            # Generate alert if high risk
            alert = self.ai_analyzer.generate_hypertension_alert(patient.patient_id, risk_assessment)
            
            return {
                'type': 'pregnancy_anc',
                'patient': patient,
                'visit': visit,
                'risk_assessment': risk_assessment,
                'alert': alert
            }
            
        except Exception as e:
            return {'error': str(e), 'type': 'error'}