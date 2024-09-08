from fastapi import Request, Depends
from services.auth import get_current_user
from schemas.UserSchemas import UserResponse

async def add_user_to_context(request: Request, current_user: UserResponse = Depends(get_current_user)):
    request.state.current_user = current_user
    return current_user