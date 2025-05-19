from typing import Optional

from pydantic import BaseModel

from app.schemas.user import User


class TokenPayload(BaseModel):
    sub: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithUser(Token):
    user: User