from fastapi import APIRouter, HTTPException, BackgroundTasks, status

from app.models.users import UserReturn, UserRegister, UserCreate
from app.crud.users import (
    SessionDep,
    get_user_by_email,
    create_user,
    get_user_by_username,
)
from app.utils.email import generate_new_account_email, send_email

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
        HTTPException: Si el usuario ya existe en el sistema.

    Returns:
        UserReturn: Usuario registrado.
    """

    user = get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )
    user = get_user_by_username(session=session, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system",
        )

    user_create = UserCreate.model_validate(user_in)
    user = create_user(session=session, user_in=user_create)
    if user_in.email:
        if user_in.full_name:
            username = user_in.full_name
        else:
            username = user_in.username

        email_data = generate_new_account_email(
            email_to=user_in.email, username=username
        )

        background_tasks.add_task(
            send_email,
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user
