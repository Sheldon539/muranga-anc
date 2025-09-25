class CentralizedDataStore:
    def __init__(self):
        self.patients = {}
        self.lab_results = []
        self.clinical_notes = []
        self.patient_index = {}
    
    def store_patient(self, patient):
        self.patients[patient.patient_id] = patient
        return patient.patient_id
    
    def store_lab_result(self, result, patient_id: str):
        self.lab_results.append(result)
        if patient_id not in self.patient_index:
            self.patient_index[patient_id] = []
        self.patient_index[patient_id].append(f"lab_result_{len(self.lab_results)-1}")
    
    def store_clinical_note(self, note, patient_id: str):
        self.clinical_notes.append(note)
        if patient_id not in self.patient_index:
            self.patient_index[patient_id] = []
        self.patient_index[patient_id].append(f"clinical_note_{len(self.clinical_notes)-1}")
    
    def get_patient_data(self, patient_id: str) -> dict:
        if patient_id not in self.patient_index:
            return {}
        
        patient_data = {
            'patient': self.patients.get(patient_id),
            'lab_results': [],
            'clinical_notes': []
        }
        
        for data_ref in self.patient_index[patient_id]:
            if data_ref.startswith('lab_result_'):
                index = int(data_ref.split('_')[-1])
                patient_data['lab_results'].append(self.lab_results[index])
            elif data_ref.startswith('clinical_note_'):
                index = int(data_ref.split('_')[-1])
                patient_data['clinical_notes'].append(self.clinical_notes[index])
        
        return patient_data