from app.models import FileRecord
from datetime import datetime

DEPT_CODES = {
    "Public Benefit Organisations Regulatory Authority": "PBORA",
    "Ministry of Interior and National Planning": "MIN",
    "PBO": "PBO",
}

def generate_file_number(department_name):
    year = datetime.utcnow().year
    dept_code = DEPT_CODES.get(department_name, "XXX")
    
    # Count existing files for sequential ID
    count = FileRecord.query.filter(FileRecord.department==department_name).count() + 1
    seq_id = str(count).zfill(5)  # 5 digits
    
    return f"GOV-{year}-{dept_code}-{seq_id}"
