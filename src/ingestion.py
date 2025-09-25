import json
from .models import DataSource, Patient, LabResult, ClinicalNote

class DataIngestion:
    def __init__(self):
        self.adapters = {
            DataSource.EHR: EHRAdapter(),
            DataSource.LIS: LISAdapter(),
            DataSource.PHR: PHRAdapter()
        }
    
    def ingest_data(self, source, raw_data: str) -> dict:
        adapter = self.adapters.get(source)
        if adapter:
            return adapter.process(raw_data)
        raise ValueError(f"Unknown data source: {source}")

class EHRAdapter:
    def process(self, raw_data: str) -> dict:
        data = json.loads(raw_data)
        patient = Patient(
            data.get('patient_id'),
            data.get('name'),
            data.get('birthDate'),
            data.get('gender')
        )
        return {'type': 'patient', 'data': patient}

class LISAdapter:
    def process(self, raw_data: str) -> dict:
        segments = raw_data.split('|')
        result = LabResult(
            segments[3] if len(segments) > 3 else 'Unknown',
            segments[5] if len(segments) > 5 else '',
            segments[6] if len(segments) > 6 else '',
            segments[7] if len(segments) > 7 else ''
        )
        return {'type': 'lab_result', 'data': result}

class PHRAdapter:
    def process(self, raw_data: str) -> dict:
        data = json.loads(raw_data)
        note = ClinicalNote(
            'patient_reported',
            data.get('symptoms', ''),
            'patient'
        )
        return {'type': 'clinical_note', 'data': note}