from fastapi import APIRouter, Depends, status, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from starlette.templating import Jinja2Templates

from ..services import DocumentService, get_current_user
from ..models.Document import DocumentPost, DocumentGetView, DocumentUpdate
from ..models.Message import Message
from ..models.User import UserGet, UserDocument

from ..settings import settings


router = APIRouter(prefix="/document", tags=["document"])

templates = Jinja2Templates(directory="templates")


@router.get("/get_document/{uuid}", response_model=DocumentGetView, responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message}
})
async def get_document_by_uuid(uuid: str,
                               document_service: DocumentService = Depends()):
    document = await document_service.get_document_by_uuid(uuid)
    if document is not None:
        return document
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "такого документа нет"}
        )


@router.post("/", responses={status.HTTP_201_CREATED: {"message": "create document"},
                             status.HTTP_406_NOT_ACCEPTABLE: {"message": "not admin"}})
async def add_document(document: DocumentPost,
                       document_service: DocumentService = Depends(),
                       user: UserGet = Depends(get_current_user)):
    if user.type.name == "admin":
        await document_service.add(document)
        return JSONResponse(content={"message": "create document"},
                            status_code=status.HTTP_201_CREATED)
    return JSONResponse(content={"message": "not admin"},
                        status_code=status.HTTP_406_UNAUTHORIZED)


@router.get("/page_document", response_model=list[DocumentGetView],
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message}
            })
async def get_document_page(response: Response,
                            page: int = 1,
                            current_user: UserGet = Depends(get_current_user),
                            doc_service: DocumentService = Depends()):
    if current_user.type.name == "admin":
        count_page = await doc_service.get_count_page()
        response.headers["X-Count-Page"] = str(count_page)
        response.headers["X-Count-Item"] = str(doc_service.count_item)
        return await doc_service.get_document_page(page)
    else:
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            content={"message": "отказ в доступе"})


@router.get("/get_url/{uuid}", responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
}, response_model=Message)
async def get_url_document(uuid: str,
                           doc_service: DocumentService = Depends()):
    url = await doc_service.get_url_document(uuid)
    return Message(
        message=url
    )


@router.get("/view_document/{uuid}")
async def view_document(uuid: str, request: Request):
    return RedirectResponse(f"https://oauth.yandex.ru/authorize?response_type=code&client_id={settings.client_id}&state={uuid}")


@router.get("/auth/yandex/token", responses={
    status.HTTP_404_NOT_FOUND: {"model": Message}
})
async def get_token_user(state: str,
                         code: str,
                         cid: str,
                         document_server: DocumentService = Depends()):
    token = await document_server.get_token_user_from_yandex(code)
    if token:
        user = await document_server.get_user_from_yandex(token)

        try:
            document = await document_server.redirect_file(user, state)
            return RedirectResponse(document.url_document)
        except Exception:
            return RedirectResponse(f"http://{settings.cors_host}:{settings.cors_port}/access_denied")
            #return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
            #                    content={"message": "отказ в доступе"})
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                        content={"message": "отказ в доступе"})


@router.delete("/{uuid}", responses={
    status.HTTP_200_OK: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message}
})
async def delete_document(uuid: str,
                          current_user: UserGet = Depends(get_current_user),
                          document_server: DocumentService = Depends()):
    if current_user.type.name == "admin":
        await document_server.delete_document(uuid)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"message": "удалено"})
    else:
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            content={"message": "отказ в доступе"})


@router.put("/", responses={
    status.HTTP_205_RESET_CONTENT: {},
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def update(document: DocumentUpdate,
                 current_user: UserGet = Depends(get_current_user),
                 document_service: DocumentService = Depends()):
    if current_user.type.name == "admin":
        await document_service.update_document(document)
        return JSONResponse(status_code=status.HTTP_205_RESET_CONTENT,
                            content={})
    else:
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            content={"message": "отказ в доступе"})


@router.get("/get_user_in_document/{uuid}", response_model=list[UserDocument],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
            })
async def get_users_to_document(uuid: str,
                                current_user: UserGet = Depends(get_current_user),
                                document_service: DocumentService = Depends()):
    if current_user.type.name == "admin":
        users = await document_service.get_users_to_document(uuid)
        return users

    else:
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            content={"message": "отказ в доступе"})