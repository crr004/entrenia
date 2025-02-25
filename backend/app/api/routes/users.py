from fastapi import APIRouter, Depends, status

from app.crud.users import get_current_admin, SessionDep
from app.models.users import UsersReturn
from app.crud.users import get_all_users


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
    response_model=UsersReturn,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> UsersReturn:
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
