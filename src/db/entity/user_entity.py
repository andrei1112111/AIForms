from sqlalchemy import Column, INTEGER, TEXT, ForeignKey
from sqlalchemy.orm import relationship

from .base_entity import Base


class User(Base):
    __tablename__ = "users"

    id = Column(INTEGER, primary_key=True)
    token = Column(TEXT, nullable=False)
    refresh_token = Column(TEXT, nullable=False)
    token_url = Column(TEXT, nullable=False)
    client_id = Column(TEXT, nullable=False)
    client_secret = Column(TEXT, nullable=False)
    scopes = Column(TEXT, nullable=False)
    email = Column(TEXT, nullable=False)

    forms = relationship(
        "Form",
        back_populates="user",
        cascade="all, delete-orphan"
    )
