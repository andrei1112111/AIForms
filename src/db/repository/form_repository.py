from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.db.entity import Form

logger = logging.getLogger(__name__)


class FormRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, form: Form):
        self.session.add(form)
        try:
            self.session.commit()
        except Exception as e:
            logger.warning(f"Failed to add project: {e}")
            self.session.rollback()
    
    def get_by_id(self, id: int) -> Optional[Form]:
        return self.session.query(Form).filter(Form.id == id).first()

    def get_forms_by_user_id(self, id: int) -> List[Form]:
        return self.session.query(Form).filter(Form.creator_id == id).all()

    def get_by_chat_link(self, chat_link: str) -> Optional[Form]:
        return self.session.query(Form).filter(Form.chat_link == chat_link).first()
    
    def get_by_title(self, title: str) -> Optional[Form]:
        return self.session.query(Form).filter(Form.title == title).first()

    def get_all(self) -> List[Form]:
        return self.session.query(Form).all()

    def delete(self, form: Form):
        try:
            self.session.delete(form)
            self.session.commit()
        except Exception as e:
            logger.warning(f"Failed to delete form {form.id}: {e}")
            self.session.rollback()
