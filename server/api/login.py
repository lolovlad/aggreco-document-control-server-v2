from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from ..models.UserLogin import UserLogin, Token, RedirectYandex
from ..models.Message import Message
from ..services import LoginServices

router = APIRouter(prefix="/login")


@router.post("/sign-in", response_model=Token, responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message}
})
async def sign_in(request: Request,
                  form_data: OAuth2PasswordRequestForm = Depends(),
                  login_services: LoginServices = Depends()):

    user = await login_services.login_user(UserLogin(email=form_data.username,
                                                     password=form_data.password), request)
    if user:
        return user
    else:
        return JSONResponse(content={"message": "неправильный логи или пароль"},
                            status_code=status.HTTP_406_NOT_ACCEPTABLE)


@router.post("/sign-in/yandex", response_model=RedirectYandex, responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message}
})
async def sign_in_yandex(user_login: UserLogin,
                         login_services: LoginServices = Depends()):
    url = await login_services.get_url_yandex(user_login)
    if url is None:
        return JSONResponse(content={"message": "неправильный логи или пароль"},
                            status_code=status.HTTP_406_NOT_ACCEPTABLE)
    return url


@router.get("/refresh", response_model=Token, responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message}
})
async def refresh(refresh_token: str,
                  login_servers: LoginServices = Depends()):

    try:
        token = await login_servers.refresh_token(refresh_token)
        return token
    except:
        return JSONResponse(content={"message": "Токен устарел"},
                            status_code=status.HTTP_406_NOT_ACCEPTABLE)


@router.get("/code_access/{code}", response_model=Token, responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message}
})
async def code_access(
        code: str,
        token: str,
        login_services: LoginServices = Depends()):
    token = await login_services.get_token_code(code, token)
    if token:
        return token
    else:
        return JSONResponse(content={"message": "Почта не совпадает"},
                            status_code=status.HTTP_406_NOT_ACCEPTABLE)