from .form_repository import FormRepository
from .user_repository import UserRepository

from db.session import Session


formRepository = FormRepository(Session())
userRepository = UserRepository(Session())

__all__ = [
    "formRepository",
    "userRepository"
]
