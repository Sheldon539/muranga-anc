# src/hypertension_ai.py
from datetime import datetime
from enum import Enum

class PregnancyRiskLevel(Enum):
    LOW = "Low Risk"
    MODERATE = "Moderate Risk"
    HIGH = "High Risk"
    CRITICAL = "Critical Risk - Refer Immediately"

class HypertensionAIAnalyzer:
    def __init__(self):
        self.hypertension_alerts = []
    
    def analyze_pregnancy_hypertension_risk(self, patient_data: dict) -> dict:
        """
        Analyze hypertension risk for pregnant women based on:
        - Blood pressure readings
        - Urinalysis protein levels
        - Gestational age
        - Medical history
        - Symptoms
        """
        risk_factors = []
        score = 0
        
        # Blood Pressure Analysis
        systolic = patient_data.get('systolic_bp', 0)
        diastolic = patient_data.get('diastolic_bp', 0)
        gestational_age = patient_data.get('gestational_age_weeks', 0)
        protein_uria = patient_data.get('urine_protein', 0)  # +1, +2, +3 or mg/dL
        symptoms = patient_data.get('symptoms', [])
        
        # BP Risk Scoring
        if systolic >= 140 or diastolic >= 90:
            score += 1
            risk_factors.append(f"Elevated BP ({systolic}/{diastolic})")
        
        if systolic >= 160 or diastolic >= 110:
            score += 2
            risk_factors.append(f"Severe hypertension ({systolic}/{diastolic})")
        
        # Proteinuria Risk Scoring
        if protein_uria > 0:
            if protein_uria == 1:  # +1
                score += 1
                risk_factors.append("Mild proteinuria")
            elif protein_uria == 2:  # +2
                score += 2
                risk_factors.append("Moderate proteinuria")
            elif protein_uria >= 3:  # +3 or higher
                score += 3
                risk_factors.append("Severe proteinuria")
        
        # Gestational Age Risk
        if gestational_age >= 20:
            score += 1
            risk_factors.append(f"Late gestation ({gestational_age} weeks)")
        
        # Symptom Risk Scoring
        critical_symptoms = ['severe headache', 'visual disturbances', 'epigastric pain', 
                           'shortness of breath', 'decreased urine output']
        
        for symptom in symptoms:
            if symptom.lower() in critical_symptoms:
                score += 2
                risk_factors.append(f"Symptom: {symptom}")
        
        # Medical History Risk
        history = patient_data.get('medical_history', [])
        if 'previous_preeclampsia' in history:
            score += 3
            risk_factors.append("History of preeclampsia")
        if 'chronic_hypertension' in history:
            score += 2
            risk_factors.append("Chronic hypertension")
        if 'diabetes' in history:
            score += 1
            risk_factors.append("Diabetes")
        if 'first_pregnancy' in history:
            score += 1
            risk_factors.append("Primigravida")
        if 'multiple_pregnancy' in history:
            score += 1
            risk_factors.append("Multiple pregnancy")
        
        # Determine Risk Level
        if score >= 6:
            risk_level = PregnancyRiskLevel.CRITICAL
            recommendation = "IMMEDIATE REFERRAL to specialist care"
        elif score >= 4:
            risk_level = PregnancyRiskLevel.HIGH
            recommendation = "Urgent review within 24 hours"
        elif score >= 2:
            risk_level = PregnancyRiskLevel.MODERATE
            recommendation = "Close monitoring, repeat tests in 1 week"
        else:
            risk_level = PregnancyRiskLevel.LOW
            recommendation = "Routine antenatal care"
        
        return {
            'risk_score': score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': recommendation,
            'timestamp': datetime.now()
        }
    
    def generate_hypertension_alert(self, patient_id: str, analysis_result: dict):
        """Generate alerts for high-risk patients"""
        if analysis_result['risk_level'] in [PregnancyRiskLevel.HIGH, PregnancyRiskLevel.CRITICAL]:
            alert_message = f"Hypertension Risk {analysis_result['risk_level'].value}: {analysis_result['recommendation']}"
            
            alert = {
                'patient_id': patient_id,
                'message': alert_message,
                'risk_score': analysis_result['risk_score'],
                'risk_factors': analysis_result['risk_factors'],
                'priority': 'HIGH' if analysis_result['risk_level'] == PregnancyRiskLevel.HIGH else 'CRITICAL',
                'timestamp': datetime.now()
            }
            
            self.hypertension_alerts.append(alert)
            return alert
        
        return None