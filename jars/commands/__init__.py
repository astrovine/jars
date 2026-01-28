from .auth import app as auth_app
from .user import app as user_app
from .wallet import app as wallet_app
from .traders import app as traders_app
from .subs import app as subs_app
from .keys import app as keys_app
from .payments import app as payments_app

__all__ = [
    "auth_app", 
    "user_app", 
    "wallet_app", 
    "traders_app", 
    "subs_app", 
    "keys_app",
    "payments_app"
]
