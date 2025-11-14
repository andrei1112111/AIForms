from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.db.entity import FormTable

logger = logging.getLogger(__name__)


class FormsRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, project: FormTable):
        self.session.add(project)
        try:
            self.session.commit()
        except Exception as e:
            logger.warning(f"Failed to add project: {e}")
            self.session.rollback()
    
    def get_by_id(self, creator_id: int) -> Optional[FormTable]:
        return self.session.query(FormTable).filter(FormTable.id == creator_id).first()
    
    def get_by_name(self, title: str) -> Optional[FormTable]:
        return self.session.query(FormTable).filter(FormTable.title == title).first()
    
    def get_all(self) -> List[FormTable]:
        return self.session.query(FormTable).all()
