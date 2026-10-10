from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.reflections import router as reflections_router
from app.api.v1.check_ins import history_router as check_in_history_router
from app.api.v1.check_ins import session_checkins_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(check_in_history_router)
api_router.include_router(sessions_router)
api_router.include_router(reflections_router)
api_router.include_router(session_checkins_router)
