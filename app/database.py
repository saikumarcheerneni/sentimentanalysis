from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Mongo connection (from environment variables)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)

# Allow override from env, default to sentiment_db
DB_NAME = os.getenv("MONGO_DB_NAME", "sentiment_db")
db = client[DB_NAME]

# Existing sentiments collection
collection = db["results"]  

# NEW collection for registered users
users_collection = db["users"]
