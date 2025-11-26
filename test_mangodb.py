from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_URI")

if not uri:
    raise ValueError("MONGO_URI is not set! Please check your .env file.")

print("Connecting to:", uri)
client = MongoClient(uri)

print("Databases:", client.list_database_names())
