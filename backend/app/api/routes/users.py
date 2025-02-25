from fastapi import APIRouter
from fastapi import Depends
from sqlmodel import select, func
from app.models.users import User

from app.utils.deps import get_current_user, SessionDep
from app.models.users import UsersReturn

# from app.crud.users import get_all_users


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", dependencies=[Depends(get_current_user)], response_model=UsersReturn)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100):
    """Devuelve todos los usuarios de la base de datos"""

    # users = get_all_users(session=session, skip=skip, limit=limit)

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersReturn(users=users, count=count)

    # return users
