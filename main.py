from fastapi import FastAPI , Query , status , HTTPException , Form , Body , UploadFile , File , Path , WebSocket
from fastapi.exception_handlers import http_exception_handler
# from chatroom.schemas import PersonCreateSchema , PersonResponceSchema , PersonUpdateSchema
from contextlib import asynccontextmanager
from typing import List
from fastapi.middleware.gzip import GZipMiddleware
from chatroom.routes import router
from config.database import get_db
from fastapi.responses import HTMLResponse , RedirectResponse
from fastapi.staticfiles import StaticFiles
from chatroom.i18n_routes import router as i18n_router
from chatroom.i18n.translator import load_translations
from chatroom.i18n.middleware import LanguageMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_db()
    except Exception as e:
        print(f"Error occurred while initializing database: {e}")
    load_translations()
    print("app started")
    yield
    print("app stopped")

app = FastAPI(lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LanguageMiddleware)

app.include_router(router)
app.include_router(i18n_router)


app.mount("/static", StaticFiles(directory="static"), name="static")


def render_page(filename: str) -> HTMLResponse:
    with open(f"static/{filename}", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return render_page("login.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return render_page("register.html")

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    return render_page("chat.html")

# names = [
#     { "id":1 , "name" : "ali" },
#     { "id":2 , "name" : "reza" },
#     { "id":3 , "name" : "amir" },
#     { "id":4 , "name" : "omid" },
# ]

# s=4

# @app.get("/names", status_code=status.HTTP_200_OK, response_model=List[PersonResponceSchema])
# def retervive_names(q : str | None = Query(alias="search",examples="ali", description="import your search key",default=None , max_length=50)):
#     if q :
#         return [item for item in names if q in item["name"].lower()]
#     return names

# @app.get("/name/{id}" , status_code=status.HTTP_200_OK, response_model=PersonResponceSchema)
# def retervive_name_detaile(id : int):
#     for item in names :
#         if item["id"] == id :
#             return item
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="not found...")

# @app.post("/add_name", status_code=status.HTTP_201_CREATED, response_model=PersonCreateSchema)
# def add_name(person : PersonCreateSchema):
#     global s
#     s+=1
#     obj = { "id" : s , "name" : person.name }
#     names.append(obj)
#     return  obj

# @app.put("/update", status_code=status.HTTP_202_ACCEPTED, response_model=PersonResponceSchema)
# def update_name(person : PersonUpdateSchema, id : int = Path()):
#     for item in names :
#         if item["id"] == id :
#             item["name"] = person.name
#             return item
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="not found...")

# @app.delete("/delete", status_code=status.HTTP_202_ACCEPTED)
# def delete_name(id:int):
#     for item in names :
#         if item["id"] == id :
#             names.remove(item)
#             return item
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="not found...")

# @app.post("/upload_file/")
# async def upload_file(file : UploadFile = File(...)):
#     content = await file.read()
#     return { "filename" : file.filename, "content_type" : file.content_type , "file_size" : len(content)}

# @app.post("/uploadfiles/")
# async def create_upload_files(files: list[UploadFile]):
#     return {"filenames": [file.filename for file in files]}
