from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

uri = os.getenv("MONGO_URI")

if not uri:
    raise ValueError("MONGO_URI is not set! Please check your .env file.")

print("Connecting to:", uri)
client = MongoClient(uri)

# Test connection
print("Databases:", client.list_database_names())
