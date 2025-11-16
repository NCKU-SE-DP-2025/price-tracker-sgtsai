# app/core/config.py
import os

API_KEY = os.getenv("API_KEY", "xxx")
SECRET_KEY = os.getenv("SECRET_KEY", "1892dhianiandowqd0n")   # default matches your tests
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))