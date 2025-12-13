from .auth import router as auth_router
from .events import router as events_router
from .experiments import router as experiments_router
from .segments import router as segments_router
from .users import router as users_router

__all__ = ['auth_router', 'events_router', 'experiments_router', 'segments_router', 'users_router']