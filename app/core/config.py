# from pydantic import BaseSettings, AnyUrl
# from typing import Optional

# class Settings(BaseSettings):
#     # App settings
#     APP_NAME=ARTMART
#     DEBUG=True
#     ENV=development
#     DATABASE_URL=postgresql://user:password@localhost:5432/mydb
#     SECRET_KEY=super-secret-key
#     GOOGLE_API_KEY=your-google-api-key
#     STRIPE_SECRET_KEY=your-stripe-secret-key


#     # Database settings
#     DATABASE_URL: AnyUrl = "postgresql://user:password@localhost:5432/mydb"

#     # Security
#     SECRET_KEY: str
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

#     # Third-party services
#     GOOGLE_API_KEY: Optional[str] = None
#     STRIPE_SECRET_KEY: Optional[str] = None

#     # CORS
#     ALLOWED_ORIGINS: list[str] = ["*"]

#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"

# settings = Settings()
