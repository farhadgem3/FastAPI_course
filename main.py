from fastapi import FastAPI , Query

app = FastAPI()

names = [
    { "id":1 , "name" : "ali" },
    { "id":2 , "name" : "reza" },
    { "id":3 , "name" : "amir" },
    { "id":4 , "name" : "omid" },
]

s=4

@app.get("/names")
def retervive_names(q : str | None = Query(default=None , max_length=50)):
    if q :
        return [item for item in names if q in item["name"].lower()]
    return names

@app.get("/name/{id}")
def retervive_name_detaile(id : int):
    for item in names :
        if item["id"] == id :
            return item
    return { "massage" : "not found..."}

@app.post("/add_name")
def add_name(name:str):
    global s
    s+=1
    obj = { "id" : s , "name" : name }
    names.append(obj)
    return  obj

@app.put("/update")
def update_name(id:int , name:str):
    for item in names :
        if item["id"] == id :
            item["name"] = name
            return item
    return { "massage" : "not found..."}

@app.delete("/delete")
def delete_name(id:int):
    for item in names :
        if item["id"] == id :
            names.remove(item)
            return item
    return { "massage" : "not found..."}