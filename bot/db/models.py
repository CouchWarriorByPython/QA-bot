from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Model for survey participants"""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    completed_survey = Column(Boolean, default=False)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)

    # Relationship to answers
    answers = relationship("Answer", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, completed={self.completed_survey})>"


class Answer(Base):
    """Model for survey answers"""
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    question_id = Column(Integer, nullable=False)
    answer_text = Column(Text, default="")
    custom_answer = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.now)

    # Relationship to user
    user = relationship("User", back_populates="answers")

    def __repr__(self):
        return f"<Answer(user_id={self.user_id}, question_id={self.question_id})>"