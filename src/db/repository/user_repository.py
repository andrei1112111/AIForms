from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.db.entity import User

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, project: User):
        self.session.add(project)
        try:
            self.session.commit()
        except Exception as e:
            logger.warning(f"Failed to add project: {e}")
            self.session.rollback()
    
    def get_by_id(self, id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def get_all(self) -> list[type[User]]:
        return self.session.query(User).all()

    def update_user(self, user: User) -> Optional[User]:
        try:
            self.session.commit()
            return user
        except Exception as e:
            logger.warning(f"Failed to update user {user.id}: {e}")
            self.session.rollback()
            return None
