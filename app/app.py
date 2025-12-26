from fastapi import FastAPI ,HTTPException,Depends, Form, UploadFile , File
from app.schemas import PostCreate,PostResponse, UserCreate, UserUpdate, UserRead
from app.db import  Post, create_db_and_tables,get_async_session, User, Set_Profile_page
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.images import imagekit
from pathlib import Path
import shutil
import os
import uuid
import tempfile
from app.users import auth_backend, current_active_user,fastapi_users
from app.ai import router as ai_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend),prefix="/auth/jwt",tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead,UserCreate),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead,UserUpdate),prefix="/users",tags=["auth"])
app.include_router(
    ai_router,
    dependencies=[Depends(current_active_user)] 
)

@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(""),
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None
    try:

        suffix = os.path.splitext(file.filename)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        upload_result = await imagekit.files.upload(
            file=Path(temp_file_path),
            file_name=file.filename,
            use_unique_file_name=True,
            tags=["backend-upload"]
        )

        post = Post(user_id = user.id,caption=caption, url=upload_result.url, file_name=file.filename, file_type=suffix)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        await file.close()


@app.post("/profile_update")
async def upload_file(
        file: UploadFile = File(...),
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1]
        result = await session.execute(select(Set_Profile_page).filter_by(user_id=user.id))
        old_profile = result.scalar_one_or_none()
        if old_profile:
            await session.delete(old_profile)
            await session.flush()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        upload_result = await imagekit.files.upload(
            file=Path(temp_file_path),
            file_name=file.filename,
            use_unique_file_name=True,
            tags=["backend-upload"]
        )

        post = Set_Profile_page(user_id = user.id, url=upload_result.url, file_name=file.filename, file_type=suffix)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        await file.close()









@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user),):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]
    posts_data = []
    result = await session.execute(select(User))

    users = [row[0] for row in result.all()]
    user_dict = {u.id: u.email for u in users}
    print(user_dict)
    for post in posts:
        posts_data.append({"id":str(post.id),
                           "user_id": str(post.user_id),
                           "url":str(post.url),
                           "file_name":str(post.file_name),
                           "file_type": str(post.file_type),
                           "created_at":str(post.created_at),
                           "caption":str(post.caption),
                           "is_owner": post.user_id == user.id,
                           "email": user_dict.get(post.user_id,"unknown")

                           })
    return {"posts":posts_data}
@app.delete("/posts/{post_id}")
async def get_post(post_id: str, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    try:

        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        print( user.id)
        print(post.user_id )
        if post.user_id != user.id:
            raise HTTPException(status_code=404, detail="User don't have access to this post")
        await session.delete(post)
        await session.commit()
        return {"success":True,"massage": "Post deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
