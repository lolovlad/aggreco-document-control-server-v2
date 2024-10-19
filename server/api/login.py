from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from ..models.UserLogin import UserLogin, Token
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