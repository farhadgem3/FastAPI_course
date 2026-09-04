from fastapi import APIRouter, Depends
from chatroom.i18n.translator import get_translator_dep, get_language

router = APIRouter(prefix="/i18n", tags=["i18n"])


@router.get("/hello")
async def hello(_=Depends(get_translator_dep)):
    return {"message": _("Hello, welcome!")}


@router.get("/goodbye")
async def goodbye(_=Depends(get_translator_dep)):
    return {"message": _("Goodbye, see you soon!")}


@router.get("/status")
async def status_check(_=Depends(get_translator_dep), lang: str = Depends(get_language)):
    return {
        "language": lang,
        "message": _("The service is running normally.")
    }