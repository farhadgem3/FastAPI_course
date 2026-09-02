from fastapi import APIRouter, Path, Depends, HTTPException, Query, status, Request, Response
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from chatroom.models import User, Message
from chatroom.manager import manager
from config.database import get_db
from chatroom.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_access_token, decode_refresh_token,
    get_authenticated_user, EXPIRE_MINUTES
)
from chatroom.schemas import UserRegisterSchema, UserLoginSchema, UserResponseSchema, UserUpdateSchema

router = APIRouter(tags=["users"])

# ---------- PUBLIC ROUTES (no login required) ----------

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
async def login(credentials: UserLoginSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password")

    access_token = create_access_token(username=user.username)
    refresh_token = create_refresh_token(username=user.username)

    # httponly=True -> JavaScript can never read these cookies (protects against XSS token theft)
    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, samesite="lax", max_age=EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, samesite="lax", max_age=7 * 24 * 60 * 60,
        path="/refresh"   # browser will only send this cookie back on requests to /refresh
    )
    return {"message": f"welcome {user.username}"}

@router.post("/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no refresh token found")

    username = decode_refresh_token(token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired refresh token")

    new_access_token = create_access_token(username=username)
    response.set_cookie(
        key="access_token", value=new_access_token,
        httponly=True, samesite="lax", max_age=EXPIRE_MINUTES * 60
    )
    return {"message": "access token refreshed"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/refresh")
    return {"message": "logged out"}


# ---------- PROTECTED ROUTES (login required) ----------

@router.get("/users", status_code=status.HTTP_200_OK, response_model=List[UserResponseSchema])
async def show_users(
    limit: int = Query(1, gt=0),
    page: int = Query(1, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    offset = (page - 1) * limit
    return db.query(User).offset(offset).limit(limit).all()

@router.get("/user/{id}", status_code=status.HTTP_200_OK, response_model=UserResponseSchema)
async def show_user(
    id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

@router.put("/user/{id}", status_code=status.HTTP_200_OK, response_model=UserResponseSchema)
async def update_user(
    id: int,
    user: UserUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    existing_user = db.query(User).filter(User.id == id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="user not found")

    # extra safety: only let a user edit their own account, not anyone else's
    if existing_user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you can only edit your own account")

    if user.username is not None:
        existing_user.username = user.username
    if user.password is not None:
        existing_user.hashed_password = hash_password(user.password)
    if user.age is not None:
        existing_user.age = user.age

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already taken")
    db.refresh(existing_user)
    return existing_user

@router.delete("/user/{id}", status_code=status.HTTP_200_OK, response_model=UserResponseSchema)
async def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    existing_user = db.query(User).filter(User.id == id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="user not found")

    if existing_user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you can only delete your own account")

    db.delete(existing_user)
    db.commit()
    return existing_user


# ---------- WEBSOCKET (login required, via cookie) ----------

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

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