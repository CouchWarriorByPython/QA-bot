import os
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from bot.db.models import Base, User, Answer
from bot.logger import info, error, warning, debug

# Database settings
DB_PATH = "survey_data.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)


def init_db():
    """Initialize the database with all required tables"""
    try:
        Base.metadata.create_all(bind=ENGINE)
        info("Database initialized successfully")
    except Exception as e:
        error(f"Database initialization failed: {e}")
        raise


def get_db_session():
    """Get a database session"""
    session = SessionLocal()
    try:
        return session
    except:
        session.close()
        raise


def save_user_answer(user_id: int, question_id: int, answer_text: str, custom_answer: str = ""):
    """Save a user's answer to a question using SQLAlchemy"""
    session = get_db_session()
    try:
        # Check if user exists
        user = session.query(User).filter(User.user_id == user_id).first()

        # If user doesn't exist, create them
        if not user:
            user = User(user_id=user_id, start_time=datetime.now())
            session.add(user)
            debug(f"Створено нового користувача з ID {user_id}")

        # Create and save the answer
        answer = Answer(
            user_id=user_id,
            question_id=question_id,
            answer_text=answer_text,
            custom_answer=custom_answer,
            timestamp=datetime.now()
        )
        session.add(answer)

        # Commit changes
        session.commit()
        debug(f"Збережено відповідь користувача {user_id} на питання {question_id}")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        error(f"Помилка збереження відповіді: {e}")
        return False
    finally:
        session.close()


def save_all_user_answers(user_id: int, answers: Dict[str, Any], questions_map: Dict[int, Dict[str, Any]]):
    """Save all answers from a user's completed survey"""
    session = get_db_session()
    try:
        # Check if user exists
        user = session.query(User).filter(User.user_id == user_id).first()

        # If user doesn't exist, create them
        if not user:
            user = User(user_id=user_id, start_time=datetime.now())
            session.add(user)
            session.flush()  # Flush to get the user ID if it's auto-generated
            debug(f"Створено нового користувача з ID {user_id}")

        # Save each answer
        for question_text, answer_data in answers.items():
            # Find question_id from question text
            question_id = None
            for q_id, q_info in questions_map.items():
                if q_info.get("question") == question_text:
                    question_id = q_id
                    break

            if question_id is None:
                warning(f"Не вдалося знайти ID питання для: {question_text}")
                continue

            # Process the answer
            selected = answer_data.get("selected", "")
            custom = answer_data.get("custom", "")

            # Convert list to string if it's a multiple choice answer
            if isinstance(selected, list):
                selected = " | ".join(selected)

            # Create and save the answer
            answer = Answer(
                user_id=user_id,
                question_id=question_id,
                answer_text=selected or "",
                custom_answer=custom or "",
                timestamp=datetime.now()
            )
            session.add(answer)
            debug(f"Збережено відповідь користувача {user_id} на питання {question_id}")

        # Mark survey as completed
        user.completed_survey = True
        user.end_time = datetime.now()

        # Commit all changes
        session.commit()
        info(f"Збережено всі відповіді для користувача {user_id}")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        error(f"Помилка збереження відповідей для користувача {user_id}: {e}")
        return False
    finally:
        session.close()


def get_question_answers(question_id: int) -> List[Dict[str, Any]]:
    """Get all answers for a specific question"""
    session = get_db_session()
    try:
        # Query answers for this question
        answers_query = session.query(Answer).filter(Answer.question_id == question_id).all()

        # Format the results
        answers = []
        for answer in answers_query:
            answers.append({
                "user_id": answer.user_id,
                "answer_text": answer.answer_text,
                "custom_answer": answer.custom_answer,
                "timestamp": answer.timestamp
            })

        debug(f"Отримано {len(answers)} відповідей на питання {question_id}")
        return answers
    except SQLAlchemyError as e:
        error(f"Помилка отримання відповідей для питання {question_id}: {e}")
        return []
    finally:
        session.close()


def get_all_answers() -> Dict[int, List[Dict[str, Any]]]:
    """Get all answers for all questions"""
    session = get_db_session()
    try:
        # Query all answers
        answers_query = session.query(Answer).all()

        # Group by question_id
        answers_by_question = {}
        for answer in answers_query:
            question_id = answer.question_id

            if question_id not in answers_by_question:
                answers_by_question[question_id] = []

            answers_by_question[question_id].append({
                "user_id": answer.user_id,
                "answer_text": answer.answer_text,
                "custom_answer": answer.custom_answer,
                "timestamp": answer.timestamp
            })

        info(f"Отримано дані для {len(answers_by_question)} питань")
        return answers_by_question
    except SQLAlchemyError as e:
        error(f"Помилка отримання всіх відповідей: {e}")
        return {}
    finally:
        session.close()


def get_survey_stats():
    """Get statistics about the survey responses"""
    session = get_db_session()
    try:
        # Get total users
        total_users = session.query(func.count(User.user_id)).scalar() or 0

        # Get completed surveys
        completed_surveys = session.query(func.count(User.user_id)).filter(User.completed_survey == True).scalar() or 0

        # Get total answers
        total_answers = session.query(func.count(Answer.id)).scalar() or 0

        stats = {
            "total_users": total_users,
            "completed_surveys": completed_surveys,
            "total_answers": total_answers,
            "completion_rate": (completed_surveys / total_users * 100) if total_users > 0 else 0
        }

        info(f"Статистика опитування: {stats}")
        return stats
    except SQLAlchemyError as e:
        error(f"Помилка отримання статистики опитування: {e}")
        return {
            "total_users": 0,
            "completed_surveys": 0,
            "total_answers": 0,
            "completion_rate": 0
        }
    finally:
        session.close()