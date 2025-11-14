from sqlalchemy import Column, INTEGER, TEXT, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base_entity import Base


class FormTable(Base):
    __tablename__ = "forms"

    content = Column(JSONB, nullable=False)

    title = Column(TEXT, nullable=False)
    link = Column(TEXT, nullable=False)
    creator_id = Column(INTEGER, ForeignKey("users.id"), nullable=False)

    creator = relationship("UsersTable", back_populates="")

