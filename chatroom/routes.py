from fastapi import APIRouter, Path,Depends,HTTPException,Query,status
from chatroom.models import User , Message
from sqlalchemy.orm import Session
from config.database import get_db
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from chatroom.manager import manager
from sqlalchemy.exc import IntegrityError
from chatroom.auth import hash_password, verify_password , create_access_token, decode_access_token
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from chatroom.schemas import UserRegisterSchema, UserLoginSchema, UserResponseSchema , UserUpdateSchema




router = APIRouter(tags=["users"])

# def get_curent_user(credentials: HTTPBasicCredentials = Depends(HTTPBasic()), db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.username == credentials.username).first()
#     if not user or not verify_password(credentials.password, user.hashed_password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password" , headers={"WWW-Authenticate": "Basic"},)
#     return user

@router.get("/users", status_code=status.HTTP_200_OK,response_model=List[UserResponseSchema])
async def show_users(limit: int = Query(1, gt=0, description="inter your limit ..."),
                     page : int = Query(1, gt=0, description="inter your page ...")
                     , db:Session = Depends(get_db)):
    offest = (page - 1) * limit
    query = db.query(User).offset(offest).limit(limit).all()
    return query

@router.get("/user/{id}", status_code=status.HTTP_200_OK, response_model=UserResponseSchema)
async def show_user(id:int = Path(...,gt=0,description="inter your id ..."), db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

@router.post("/user", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchema)
async def create_user(user:UserRegisterSchema, db:Session = Depends(get_db)):
    new_user = User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/user/{id}", status_code=status.HTTP_200_OK, response_model=UserResponseSchema)
async def update_user(id:int, user:UserUpdateSchema, db:Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="user not found")
    if user.username is not None:
        existing_user.username = user.username
    if user.password is not None:
        existing_user.hashed_password = hash_password(user.password)
    if user.age is not None:
        existing_user.age = user.age
    db.commit()
    db.refresh(existing_user)
    return existing_user

@router.delete("/user/{id}", status_code=status.HTTP_200_OK, response_model=UserResponseSchema)
async def delete_user(id:int, db:Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="user not found")
    db.delete(existing_user)
    db.commit()
    return existing_user

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchema)
async def register(user: UserRegisterSchema, db: Session = Depends(get_db)):
    new_user = User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already taken")
    db.refresh(new_user)
    return new_user

@router.post("/login")
async def login(credentials: UserLoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password")
    # return {"message": f"welcome {user.username}, you can now connect to the chat"}
    token = create_access_token(username=user.username)
    return {"access_token": token, "token_type": "bearer"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    username = decode_access_token(token)
    if username is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user = db.query(User).filter(User.username == username).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)

    history = db.query(Message).order_by(Message.timestamp.asc()).all()
    for msg in history:
        formatted = f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {msg.user.username}: {msg.content}"
        await manager.send_personal_message(formatted, websocket)

    await manager.broadcast(f"[ {username} joined the chat ]")

    try:
        while True:
            data = await websocket.receive_text()

            new_message = Message(content=data, user_id=user.id)
            db.add(new_message)
            db.commit()

            formatted = f"[{new_message.timestamp.strftime('%Y-%m-%d %H:%M')}] {username}: {data}"
            await manager.broadcast(formatted)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"[ {username} left the chat ]")