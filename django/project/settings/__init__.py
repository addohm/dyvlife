import os

def get_secret(secret_id, backup=None):
    return os.getenv(secret_id, backup)

# Keep at the end
if get_secret('PIPELINE') == 'production':
    from .production import *
    print("Loading production environment settings...")
else:
    from .development import *
    print("Loading development environment settings...")