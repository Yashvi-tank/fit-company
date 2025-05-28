import jwt
import datetime
from typing import Optional, Callable
from functools import wraps
from flask import request, jsonify, g
from ..models_db import UserModel
from ..database import db_session
from ..services.user_service import verify_password  # ✅ use this instead of hash_password

SECRET_KEY = "fit-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

def authenticate_user(email: str, password: str) -> Optional[UserModel]:
    """
    Authenticate a user by email and password
    """
    db = db_session()
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None
        
        # ✅ Use proper password comparison
        if not verify_password(user.password_hash, password):
            return None

        return user
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Create a JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

    return encoded_jwt

def decode_token(token: str) -> dict:
    """
    Decode a JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

def admin_required(f: Callable) -> Callable:
    """
    Decorator to require admin role for an endpoint
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({"error": "Invalid authorization header format"}), 401

        token = parts[1]
        payload = decode_token(token)

        if "error" in payload:
            return jsonify({"error": payload["error"]}), 401

        if payload.get("role") != "admin":
            return jsonify({"error": "Admin privileges required"}), 403

        return f(*args, **kwargs)

    return decorated_function

def jwt_required(f: Callable) -> Callable:
    """
    Decorator to require a valid JWT token and set the user identity in Flask's g object
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({"error": "Invalid authorization header format"}), 401

        token = parts[1]
        payload = decode_token(token)

        if "error" in payload:
            return jsonify({"error": payload["error"]}), 401

        g.user_email = payload.get("sub")
        return f(*args, **kwargs)

    return decorated_function
