import os
from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from app.crud.users import SessionDep, get_user_by_email, update_password
from app.utils.users import authenticate_user
from app.models.tokens import Token
from app.models.messages import Message
from app.models.users import NewPassword
from app.utils.tokens import (
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.utils.email import generate_password_reset_email, send_email
from app.utils.hashing import hash_password, verify_password

router = APIRouter(prefix="/login", tags=["login"])


@router.post("/", status_code=status.HTTP_200_OK, response_model=Token)
async def login_user(
    session: SessionDep, data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """Obtiene un token de acceso para un usuario.

    Args:
        session (SessionDep): Sesión de la base de datos.
        data (OAuth2PasswordRequestForm): Datos del usuario.

    Raises:
        HTTPException[401]: Si el nombre de usuario/email o la contraseña son incorrectos.
        HTTPException[403]: Si el usuario no está verificado o su cuenta está desactivada.

    Returns:
        Token: Token de acceso.
    """

    user = await authenticate_user(
        session=session, email_or_username=data.username, password=data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    elif not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Unverified user"
        )
    acces_token_expire = timedelta(minutes=int(os.environ["ACCESS_TOKEN_EXPIRE"]))
    return Token(
        access_token=create_access_token(
            subject=user.id, expires_delta=acces_token_expire
        )
    )


@router.post("/password-recovery/{email}")
async def recover_password(
    session: SessionDep, email: str, background_tasks: BackgroundTasks
) -> Message:
    """Manda un correo al usuario para que restablezca su contraseña a través de un token.

    Args:
        session (SessionDep): Sesión de la base de datos.
        email (str): Email del usuario.
        background_tasks (BackgroundTasks): Tareas en segundo plano.

    Raises:
        HTTPException[404]: Si el usuario con ese correo no se encuentra en el sistema.
        HTTPException[403]: Si el usuario no está verificado o su cuenta está desactivada.

    Returns:
        Message: Mensaje de confirmación.
    """

    user = await get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    elif not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Unverified user"
        )

    password_reset_token = create_password_reset_token(email=email)
    if user.full_name:
        username = user.full_name
    else:
        username = user.username
    email_data = generate_password_reset_email(
        email_to=user.email, username=username, token=password_reset_token
    )

    background_tasks.add_task(
        send_email,
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/password-reset/")
async def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """Verifica el token y restablece la contraseña.

    Args:
        session (SessionDep): Sesión de la base de datos.
        body (NewPassword): Token y nueva contraseña.

    Raises:
        HTTPException[400]: Si el token no es válido o la contraseña está repetida.
        HTTPException[404]: Si no existe un usuario con ese email.
        HTTPException[403]: Si la cuenta del usuario está desactivada.

    Return:
        Message: Mensaje de confirmación.
    """

    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
    user = await get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    if verify_password(plain_password=body.new_password, hashed_password=user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot reuse you previous password",
        )

    hashed_password = hash_password(password=body.new_password)
    user = await update_password(
        session=session, user=user, new_password=hashed_password
    )
    return Message(message="Password updated successfully")
