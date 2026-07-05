from models.user import User
from sqlalchemy.orm import Session
from logging import getLogger

logger = getLogger(__name__)

def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieve a user by email."""
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as error:
        logger.error(f"Failed (get_user_by_email) to database: {error}")
        return None


def create_user(db: Session, user: User) -> User | None:
    """Create a new user in the database."""
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as error:
        logger.error(f"Failed (create_user) to database: {error}")
        return None


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Retrieve a user by email."""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception as error:
        logger.error(f"Failed (get_user_by_id) to database: {error}")
        return None
