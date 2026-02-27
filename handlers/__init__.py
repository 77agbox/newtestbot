from .start import router as start_router
from .support import router as support_router
from .packages import router as packages_router
from .admin import router as admin_router
from .clubs import router as clubs_router
from .masterclasses import router as masterclasses_router


def register_handlers(dp):
    dp.include_router(start_router)
    dp.include_router(support_router)
    dp.include_router(packages_router)
    dp.include_router(admin_router)
    dp.include_router(clubs_router)
    dp.include_router(masterclasses_router)
