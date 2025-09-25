import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models import Patient, DataSource

# Test basic functionality
patient = Patient("P001", "John Doe", "1980-01-15", "male")
print(f"✅ Patient created: {patient.name}")

print(f"✅ Data sources: {[ds.value for ds in DataSource]}")
print("✅ Basic setup working!")