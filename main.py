
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from bson import ObjectId
from bson.errors import InvalidId

from models.auth import RegisterUser, LoginUser
from utils.security import hash_password, verify_password
from database.mongodb import auth_collection, users_collection

app = FastAPI(
    title="AI Interview Copilot",
    description="Backend API for user registration, login, and user management",
    version="1.0.0"
)


# -------------------------
# USER MODEL
# -------------------------
class User(BaseModel):
    name: str
    email: EmailStr


# -------------------------
# HOME
# -------------------------
@app.get("/")
async def home():
    return {
        "message": "AI Interview Copilot is running"
    }


# -------------------------
# REGISTER
# -------------------------
@app.post("/register/", status_code=201)
async def register(user: RegisterUser):
    name = user.name.strip()
    email = user.email.strip().lower()

    if not name or not email or not user.password:
        raise HTTPException(
            status_code=400,
            detail="Name, email and password are required"
        )

    # bcrypt supports passwords up to 72 bytes
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must not exceed 72 bytes"
        )

    existing_user = await auth_collection.find_one(
        {"email": email}
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = {
        "name": name,
        "email": email,
        "password": hashed_password
    }

    result = await auth_collection.insert_one(new_user)

    return {
        "message": "User registered successfully",
        "id": str(result.inserted_id)
    }


# -------------------------
# LOGIN
# -------------------------
@app.post("/login")
async def login(user: LoginUser):
    email = user.email.strip().lower()

    existing_user = await auth_collection.find_one(
        {"email": email}
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_hash = existing_user.get("password")

    if not password_hash or not verify_password(
        user.password,
        password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "id": str(existing_user["_id"]),
        "name": existing_user["name"]
    }


# -------------------------
# CREATE USER
# -------------------------
@app.post("/users", status_code=201)
async def create_user(user: User):
    email = str(user.email).strip().lower()

    existing_user = await users_collection.find_one(
        {"email": email}
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    new_user = {
        "name": user.name.strip(),
        "email": email
    }

    result = await users_collection.insert_one(new_user)

    return {
        "message": "User added successfully",
        "id": str(result.inserted_id)
    }


# -------------------------
# GET ALL USERS
# -------------------------
@app.get("/users")
async def get_users():
    users = []

    # Exclude password hashes from API responses
    async for user in users_collection.find(
        {},
        {"password": 0}
    ):
        user["_id"] = str(user["_id"])
        users.append(user)

    return users


# -------------------------
# GET SINGLE USER
# -------------------------
@app.get("/users/{id}")
async def get_user(id: str):
    try:
        object_id = ObjectId(id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    user = await users_collection.find_one(
        {"_id": object_id},
        {"password": 0}
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user["_id"] = str(user["_id"])
    return user


# -------------------------
# UPDATE USER
# -------------------------
@app.put("/users/{id}")
async def update_user(id: str, user: User):
    try:
        object_id = ObjectId(id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    email = str(user.email).strip().lower()

    existing_email = await users_collection.find_one({
        "email": email,
        "_id": {"$ne": object_id}
    })

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    result = await users_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "name": user.name.strip(),
                "email": email
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "message": "User updated successfully"
    }


# -------------------------
# DELETE USER
# -------------------------
@app.delete("/users/{id}")
async def delete_user(id: str):
    try:
        object_id = ObjectId(id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    result = await users_collection.delete_one(
        {"_id": object_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "message": "User deleted successfully"
    }
