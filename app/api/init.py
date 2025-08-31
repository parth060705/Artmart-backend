# from fastapi import APIRouter
# from . import routes

# router = APIRouter()
# router.include_router(routes.router)


import pkgutil
import importlib

# Dynamically import all modules inside the 'api' package
for module_info in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_info.name}")
