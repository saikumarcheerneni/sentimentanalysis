from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)

DB_NAME = os.getenv("MONGO_DB_NAME", "sentiment_db")
db = client[DB_NAME]

collection = db["results"]  

users_collection = db["users"]

activity_collection = db["activity_logs"]

performance_collection = db["performance_logs"]

