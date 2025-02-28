import re

from fastapi import APIRouter, HTTPException, BackgroundTasks, status

from app.models.users import UserReturn, UserRegister, UserCreate
from app.crud.users import (
    SessionDep,
    get_user_by_email,
    create_user,
    get_user_by_username,
    update_user,
)
from app.utils.email import generate_new_account_email, send_email
from app.utils.tokens import create_verify_account_token, verify_user_verification_token
from app.models.messages import Message

router = APIRouter(prefix="/signup", tags=["signup"])


@router.post("/", response_model=UserReturn)
def register_user(
    session: SessionDep, user_in: UserRegister, background_tasks: BackgroundTasks
) -> UserReturn:
    """Registra un nuevo usuario en el sistema.

    Args:
        session (SessionDep): Sesión de la base de datos.
        user_in (UserRegister): Datos del usuario a registrar.
        background_tasks (BackgroundTasks): Tareas en segundo plano.

    Raises:
        HTTPException[409]: Si el usuario ya existe en el sistema.
        HTTPException[400]: Si los campos no cumplen las restricciones.

    Returns:
        UserReturn: Usuario registrado.
    """

    user = get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this email already exists in the system",
        )
    user = get_user_by_username(session=session, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this username already exists in the system",
        )

    if not re.match(r"^(?=.*[a-z]{3})[a-z0-9_]+$", user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The username can only contain lowercase letters, numbers and underscores, and must contain at least 3 letters",
        )

    if user_in.full_name:
        if not re.match(
            r"^[A-Za-zÁ-ÿà-ÿ]+(?:[ '-][A-Za-zÁ-ÿà-ÿ]+)*$", user_in.full_name
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The full name field has invalid characters",
            )

    user_create = UserCreate.model_validate(user_in)

    user = create_user(session=session, user_in=user_create)

    verify_account_token = create_verify_account_token(email=user.email)

    if user.email:
        if user.full_name:
            username = user.full_name
        else:
            username = user.username

        email_data = generate_new_account_email(
            email_to=user.email, username=username, token=verify_account_token
        )

        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.post("/account-verification/")
def verify_account(session: SessionDep, token: str) -> Message:
    """Verifica el token y marca como verificada la cuenta del usuario.

    Args:
        session (SessionDep): Sesión de la base de datos.
        token (Token): Token.

    Raises:
        HTTPException[400]: Si el token no es válido.
        HTTPException[404]: Si no existe un usuario con ese email.
        HTTPException[409]: Si la cuenta ya está verificada.

    Return:
        Message: Mensaje de confirmación.
    """

    email = verify_user_verification_token(token=token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
    user = get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system",
        )
    elif user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user is already verified",
        )
    user.is_verified = True
    user_data = user.model_dump(exclude_unset=True)
    user = update_user(session=session, user=user, user_data=user_data)
    return Message(message="User verified successfully")
