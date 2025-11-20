from sqlalchemy import Column, INTEGER, TEXT, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base_entity import Base


class Form(Base):
    __tablename__ = "forms"

    id = Column(INTEGER, primary_key=True)

    content = Column(JSONB, nullable=False)

    title = Column(TEXT, nullable=False)
    link = Column(TEXT, nullable=False)
    creator_id = Column(INTEGER, ForeignKey("users.id"), nullable=False)

    creator = relationship(
        "User",
        back_populates="forms",
    )

