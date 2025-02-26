from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks

from app.crud.users import get_current_admin, SessionDep, get_user_by_email
from app.models.users import UsersReturn, UserReturn, UserCreate
from app.crud.users import get_all_users, create_user
from app.utils.email import generate_new_account_email, send_email


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
    response_model=UsersReturn,
)
def admin_read_users(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> UsersReturn:
    """Devuelve todos los usuarios de la base de datos

    Args:
        session (SessionDep): Sesión de la base de datos
        skip (int, optional): Cantidad de usuarios a omitir. Por defecto 0.
        limit (int, optional): Cantidad de usuarios a devolver. Por defecto 100.

    Returns:
        UsersReturn: Lista de usuarios
    """

    users = get_all_users(session=session, skip=skip, limit=limit)

    return users


@router.post("/", dependencies=[Depends(get_current_admin)], response_model=UserReturn)
def admin_create_user(
    *, session: SessionDep, user_in: UserCreate, background_tasks: BackgroundTasks
) -> UserReturn:
    """Crea un nuevo usuario en la base de datos.

    Args:
        session (SessionDep): Sesión de la base de datos.
        user_in (UserCreate): Datos del usuario a crear.

    Returns:
        UserReturn: Usuario creado.
    """

    user = get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )

    user = create_user(session=session, user_in=user_in)
    if user_in.email:
        if user_in.full_name:
            username = user_in.full_name
        else:
            username = user_in.username

        email_data = generate_new_account_email(
            email_to=user_in.email, username=username, password=user_in.password
        )

        background_tasks.add_task(
            send_email,
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user
