from pymongo import MongoClient
import config

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]

users = db['users']
job_seekers = db['job_seekers']
recruiters = db['recruiters']
jobs = db['jobs']
resumes = db['resumes']
applications = db['applications']

# Ek email se sirf ek account (technical doc ka rule)
users.create_index('email', unique=True)

# Ek seeker ek job pe sirf ek baar apply kar sake (duplicate pe MongoDB khud error dega)
applications.create_index([('job_id', 1), ('seeker_id', 1)], unique=True)
