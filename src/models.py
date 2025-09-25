from datetime import datetime
from enum import Enum

class DataSource(Enum):
    EHR = "EHR"
    LIS = "LIS"
    PHR = "PHR"

class Patient:
    def __init__(self, patient_id: str, name: str, dob: str, gender: str):
        self.patient_id = patient_id
        self.name = name
        self.dob = dob
        self.gender = gender
        self.created_at = datetime.now()

class LabResult:
    def __init__(self, test_name: str, result: str, units: str, normal_range: str):
        self.test_name = test_name
        self.result = result
        self.units = units
        self.normal_range = normal_range
        self.timestamp = datetime.now()

class ClinicalNote:
    def __init__(self, note_type: str, content: str, author: str):
        self.note_type = note_type
        self.content = content
        self.author = author
        self.timestamp = datetime.now()
# Add to existing models.py - Pregnancy specific models

class PregnancyPatient(Patient):
    def __init__(self, patient_id: str, name: str, dob: str, gender: str, gestation_weeks: int):
        super().__init__(patient_id, name, dob, gender)
        self.gestation_weeks = gestation_weeks
        self.parity = 0  # Number of previous pregnancies
        self.medical_history = []
        self.anc_visits = []

class ANCVisit:
    def __init__(self, visit_date: str, gestation_weeks: int):
        self.visit_date = visit_date
        self.gestation_weeks = gestation_weeks
        self.systolic_bp = None
        self.diastolic_bp = None
        self.urine_protein = None  # 0, +1, +2, +3
        self.symptoms = []
        self.risk_assessment = None

class UrinalysisResult:
    def __init__(self, protein: int, glucose: int, leukocytes: int, nitrites: bool):
        self.protein = protein  # 0-3 scale or mg/dL
        self.glucose = glucose
        self.leukocytes = leukocytes
        self.nitrites = nitrites
        self.timestamp = datetime.now()