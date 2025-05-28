from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Table, Text, Date
from sqlalchemy.orm import relationship
from .database import Base

# --------------------- User Model ---------------------
class UserModel(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Onboarding profile data
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    fitness_goal = Column(String, nullable=True)
    onboarded = Column(String, default="false", nullable=False)

    # Relationship to workout history
    exercise_history = relationship("UserExerciseHistoryModel", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}', role='{self.role}')>"

# --------------------- Junction Table ---------------------
exercise_muscle_groups = Table(
    "exercise_muscle_groups",
    Base.metadata,
    Column("exercise_id", Integer, ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    Column("muscle_group_id", Integer, ForeignKey("muscle_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("is_primary", Boolean, default=False, nullable=False),
)

# --------------------- MuscleGroup Model ---------------------
class MuscleGroupModel(Base):
    __tablename__ = "muscle_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    body_part = Column(String(50), nullable=False)
    description = Column(Text)

    exercises = relationship(
        "ExerciseModel",
        secondary=exercise_muscle_groups,
        back_populates="muscle_groups"
    )

    def __repr__(self):
        return f"<MuscleGroup(id={self.id}, name='{self.name}', body_part='{self.body_part}')>"

# --------------------- Exercise Model ---------------------
class ExerciseModel(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    difficulty = Column(Integer, nullable=False)
    equipment = Column(String(100))
    instructions = Column(Text)

    muscle_groups = relationship(
        "MuscleGroupModel",
        secondary=exercise_muscle_groups,
        back_populates="exercises"
    )

    assigned_users = relationship("UserExerciseHistoryModel", back_populates="exercise", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exercise(id={self.id}, name='{self.name}', difficulty={self.difficulty})>"

# --------------------- Exercise History Model ---------------------
class UserExerciseHistoryModel(Base):
    __tablename__ = "user_exercise_history"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    date_assigned = Column(Date, nullable=False)

    user = relationship("UserModel", back_populates="exercise_history")
    exercise = relationship("ExerciseModel", back_populates="assigned_users")
