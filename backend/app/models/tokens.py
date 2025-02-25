from sqlmodel import SQLModel


class Token(SQLModel):
    """Modelo de token."""

    access_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    """Modelo de carga (contenido) del token."""

    sub: str | None = None
