from ..models_dto import UserSchema, UserResponseSchema, UserProfileSchema, UserProfileResponseSchema
from ..models_db import UserModel
from ..database import db_session
from typing import List, Optional
from werkzeug.security import generate_password_hash, check_password_hash

def generate_random_password(length=10):
    import random
    import string
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

def hash_password(password: str) -> str:
    """Hash a password using werkzeug (with salt)"""
    return generate_password_hash(password)

def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Verify a password using werkzeug"""
    return check_password_hash(hashed_password, plain_password)

def create_user(user: UserSchema) -> UserResponseSchema:
    """
    Create a new user with the provided password or a random one if not set
    """
    raw_password = getattr(user, "password", None) or generate_random_password()
    hashed_password = hash_password(raw_password)

    db_user = UserModel(
        email=user.email,
        name=user.name,
        role=user.role,
        password_hash=hashed_password
    )

    db = db_session()
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return UserResponseSchema(
        email=user.email,
        name=user.name,
        role=user.role,
        password=raw_password
    )


def authenticate_user(email: str, password: str) -> Optional[UserModel]:
    db = db_session()
    try:
        print(f"[DEBUG] Authenticating: {email}")
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            print("[ERROR] User not found in database.")
            return None

        print(f"[DEBUG] Found user: {user.email}")
        print(f"[DEBUG] Stored hash: {user.password_hash}")
        print(f"[DEBUG] Comparing with: {password}")

        if verify_password(user.password_hash, password):
            print("[DEBUG] Password verified successfully.")
            return user
        else:
            print("[ERROR] Password verification failed.")
            return None
    finally:
        db.close()


def get_all_users() -> List[UserSchema]:
    db = db_session()
    try:
        db_users = db.query(UserModel).all()
        return [
            UserSchema(
                email=user.email,
                name=user.name,
                role=user.role
            ) for user in db_users
        ]
    finally:
        db.close()

def update_user_profile(email: str, profile: UserProfileSchema) -> Optional[UserProfileResponseSchema]:
    db = db_session()
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None

        user.weight = profile.weight
        user.height = profile.height
        user.fitness_goal = profile.fitness_goal
        user.onboarded = "true"

        db.commit()
        db.refresh(user)

        return UserProfileResponseSchema(
            email=user.email,
            name=user.name,
            weight=user.weight,
            height=user.height,
            fitness_goal=user.fitness_goal,
            onboarded=user.onboarded
        )
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_user_profile(email: str) -> Optional[UserProfileResponseSchema]:
    db = db_session()
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None

        return UserProfileResponseSchema(
            email=user.email,
            name=user.name,
            weight=user.weight,
            height=user.height,
            fitness_goal=user.fitness_goal,
            onboarded=user.onboarded
        )
    finally:
        db.close()
