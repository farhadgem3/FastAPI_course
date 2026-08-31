from fastapi import FastAPI , Query , status , HTTPException , Form , Body , UploadFile , File , Path , WebSocket
from fastapi.exception_handlers import http_exception_handler
from chatroom.schemas import PersonCreateSchema , PersonResponceSchema , PersonUpdateSchema
from contextlib import asynccontextmanager
from typing import List

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("app started")
    yield
    print("app stopped")

app = FastAPI(lifespan=lifespan)

names = [
    { "id":1 , "name" : "ali" },
    { "id":2 , "name" : "reza" },
    { "id":3 , "name" : "amir" },
    { "id":4 , "name" : "omid" },
]

s=4

@app.get("/names", status_code=status.HTTP_200_OK, response_model=List[PersonResponceSchema])
def retervive_names(q : str | None = Query(alias="search",examples="ali", description="import your search key",default=None , max_length=50)):
    if q :
        return [item for item in names if q in item["name"].lower()]
    return names

@app.get("/name/{id}" , status_code=status.HTTP_200_OK, response_model=PersonResponceSchema)
def retervive_name_detaile(id : int):
    for item in names :
        if item["id"] == id :
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="not found...")

@app.post("/add_name", status_code=status.HTTP_201_CREATED, response_model=PersonCreateSchema)
def add_name(person : PersonCreateSchema):
    global s
    s+=1
    obj = { "id" : s , "name" : person.name }
    names.append(obj)
    return  obj

@app.put("/update", status_code=status.HTTP_202_ACCEPTED, response_model=PersonResponceSchema)
def update_name(person : PersonUpdateSchema, id : int = Path()):
    for item in names :
        if item["id"] == id :
            item["name"] = person.name
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="not found...")

@app.delete("/delete", status_code=status.HTTP_202_ACCEPTED)
def delete_name(id:int):
    for item in names :
        if item["id"] == id :
            names.remove(item)
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="not found...")

@app.post("/upload_file/")
async def upload_file(file : UploadFile = File(...)):
    content = await file.read()
    return { "filename" : file.filename, "content_type" : file.content_type , "file_size" : len(content)}

@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}
