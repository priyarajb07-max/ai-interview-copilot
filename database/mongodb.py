from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
print("MongoDB Connected")
client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))

db = client["ai_interview_copilot"]

users_collection = db["users"]
resumes_collection = db["resumes"]
interviews_collection = db["interviews"]    


auth_collection = db["users"]