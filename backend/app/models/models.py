from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    age = Column(Integer)  # Player's age (e.g., 6-12)
    grade = Column(Integer)  # Grade level (e.g., 1-5)
    avatar = Column(String, default="default.png")  # Avatar image filename
    created_at = Column(DateTime, default=func.now())
    
    # Default settings
    preferred_subject = Column(String, default="Math")  # "Math" or "English"
    preferred_difficulty = Column(String, default="Easy")  # "Easy", "Medium", "Hard"
    
    # Relationship
    progress = relationship("Progress", back_populates="player")


class Progress(Base):
    __tablename__ = "progress"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    
    # Question details
    question_text = Column(Text)
    question_type = Column(String)  # "multiple-choice", "direct-answer", "reading-comprehension"
    subject = Column(String)  # "Math" or "English"
    difficulty = Column(String)  # "Easy", "Medium", "Hard"
    
    # Answer details
    user_answer = Column(Text)
    correct_answer = Column(Text)
    is_correct = Column(Boolean)
    
    # Metadata
    timestamp = Column(DateTime, default=func.now())
    
    # Relationship
    player = relationship("Player", back_populates="progress") 