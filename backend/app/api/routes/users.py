import uuid

from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks

from app.models.users import (
    UsersReturn,
    UserReturn,
    UserCreate,
    UserUpdateOwn,
    UserUpdatePassword,
    UserUpdate,
)
from app.models.messages import Message
from app.utils.hashing import hash_password, verify_password
from app.crud.users import (
    get_all_users,
    create_user,
    CurrentUser,
    get_user_by_username,
    get_user_by_id,
    get_current_admin,
    SessionDep,
    get_user_by_email,
    update_user,
    update_password,
    delete_user,
    update_user_by_admin,
)
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
    """Devuelve todos los usuarios del sistema.

    Args:
        session (SessionDep): Sesión de la base de datos.
        skip (int, optional): Cantidad de usuarios a omitir. Por defecto 0.
        limit (int, optional): Cantidad de usuarios a devolver. Por defecto 100.

    Returns:
        UsersReturn: Lista de usuarios.
    """

    users = get_all_users(session=session, skip=skip, limit=limit)

    return users


@router.post("/", dependencies=[Depends(get_current_admin)], response_model=UserReturn)
def admin_create_user(
    *, session: SessionDep, user_in: UserCreate, background_tasks: BackgroundTasks
) -> UserReturn:
    """Crea un nuevo usuario en el sistema.

    Args:
        session (SessionDep): Sesión de la base de datos.
        user_in (UserCreate): Datos del usuario a crear.

    Raises:
        HTTPException: Si el usuario ya existe en la base de datos.

    Returns:
        UserReturn: Usuario creado.
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


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_admin)],
    response_model=UserReturn,
)
def admin_update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> UserReturn:
    """Actualiza los datos de un usuario dado su ID.

    Args:
        session (SessionDep): Sesión de la base de datos.
        user_id (uuid.UUID): Id del usuario a buscar.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException: Si el usuario no tiene suficientes privilegios.

    Returns:
        UserReturn: Datos del usuario.
    """

    user = get_user_by_id(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
    if user_in.username:
        existing_user = get_user_by_username(session=session, username=user_in.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username already exists",
            )

    user = update_user_by_admin(session=session, db_user=user, user_in=user_in)
    return user


@router.delete("/{user_id}", dependencies=[Depends(get_current_admin)])
def admin_delete_user(
    session: SessionDep, user_id: uuid.UUID, current_user: CurrentUser
) -> Message:
    """Elimina un usuario dado su ID.

    Args:
        session (SessionDep): Sesión de la base de datos.
        user_id (uuid.UUID): Id del usuario a buscar.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException: Si el usuario no tiene suficientes privilegios.

    Returns:
        Message: Mensaje de confirmación.
    """

    user = get_user_by_id(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    if user == current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins are not allowed to delete themselves",
        )

    delete_user(session=session, user=current_user)
    return Message(message="User deleted successfully")


@router.get("/{user_id}", response_model=UserReturn)
def read_user(
    session: SessionDep, user_id: uuid.UUID, current_user: CurrentUser
) -> UserReturn:
    """Devuelve los datos de un usuario específico dado su ID.

    Args:
        session (SessionDep): Sesión de la base de datos.
        user_id (uuid.UUID): Id del usuario a buscar.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException: Si el usuario no tiene suficientes privilegios.

    Returns:
        UserReturn: Datos del usuario.
    """

    user = get_user_by_id(session=session, id=user_id)
    if user == current_user:
        return user
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    return user


@router.get("/own", response_model=UserReturn)
def read_user_own(current_user: CurrentUser) -> UserReturn:
    """Devuelve los datos del usuario actual.

    Args:
        current_user (CurrentUser): Usuario actual.

    Returns:
        UserReturn: Datos del usuario actual.
    """
    return current_user


@router.patch("/own", response_model=UserReturn)
def update_user_own(
    *, session: SessionDep, user_in: UserUpdateOwn, current_user: CurrentUser
) -> UserReturn:
    """Actualiza los datos del usuario actual.

    Args:
        session (SessionDep): Sesión de la base de datos.
        user_in (UserUpdateOwn): Datos del usuario a actualizar.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException: Si el nombre de usuario ya existe en la base de datos.

    Returns:
        UserReturn: Usuario actualizado.
    """

    if user_in.username:
        existing_user = get_user_by_username(session=session, username=user_in.username)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username already exists",
            )
    user_data = user_in.model_dump(
        exclude_unset=True
    )  # Genera un diccionario con solo los datos que han sido modificados.

    current_user = update_user(session=session, user=current_user, user_data=user_data)

    return current_user


@router.patch("/own/password", response_model=Message)
def update_password_own(
    *, session: SessionDep, form_body: UserUpdatePassword, current_user: CurrentUser
) -> Message:
    """Actualiza la contraseña del usuario actual.

    Args:
        session (SessionDep): Sesión de la base de datos.
        body (UserUpdatePassword): Datos de la nueva contraseña.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException: Si la contraseña actual es incorrecta o si la nueva contraseña es igual a la actual.

    Returns:
        Message: Mensaje de confirmación.
    """

    if not verify_password(
        plain_password=form_body.current_password, hashed_password=current_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )
    if form_body.current_password == form_body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current one",
        )

    hashed_password = hash_password(password=form_body.new_password)
    current_user = update_password(
        session=session, user=current_user, new_password=hashed_password
    )
    return Message(message="Password updated successfully")


@router.delete("/own", response_model=Message)
def delete_user_own(session: SessionDep, current_user: CurrentUser) -> Message:
    """Elimina el usuario actual.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException: Si el usuario actual es un admin.

    Returns:
        Message: Mensaje de confirmación.
    """

    if current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins are not allowed to delete themselves",
        )
    delete_user(session=session, user=current_user)
    return Message(message="User deleted successfully")
