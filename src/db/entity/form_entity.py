from sqlalchemy import Column, INTEGER, TEXT, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import DateTime

from .base_entity import Base


class Form(Base):
    __tablename__ = "forms"

    id = Column(INTEGER, primary_key=True)

    columns = Column(JSONB, nullable=False)

    title = Column(TEXT, nullable=False)
    url = Column(TEXT, nullable=False)
    description = Column(TEXT, nullable=False)
    chat_link = Column(TEXT, nullable=False)

    created_at = Column(DateTime, server_default='NOW()')

    creator = relationship(
        "User",
        back_populates="forms",
    )

