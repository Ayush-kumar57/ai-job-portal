import os

# Project ka main folder (ai-job-portal/) - isse baaki paths banate hain
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONGO_URI = 'mongodb://localhost:27017'
DB_NAME = 'job_portal'
SECRET_KEY = 'change-this-to-any-random-text'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'resumes')
ALLOWED_EXT = {'pdf', 'docx'}
MAX_FILE_MB = 2
