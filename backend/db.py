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
