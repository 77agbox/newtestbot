from .admin import register_admin_handlers
from .clubs import register_club_handlers
from .masterclasses import register_masterclass_handlers
from .packages import register_package_handlers
from .start import register_start_handlers
from .support import register_support_handlers

def register_handlers(dp):
    register_start_handlers(dp)
    register_admin_handlers(dp)
    register_club_handlers(dp)
    register_masterclass_handlers(dp)
    register_package_handlers(dp)
    register_support_handlers(dp)
