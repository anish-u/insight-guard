from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
  env: str = Field(default="development", alias="ENV")

  api_port: int = Field(default=8000, alias="API_PORT")

  neo4j_uri: str = Field(default="bolt://neo4j:7687", alias="NEO4J_URI")
  neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
  neo4j_password: str = Field(default="NEO4J_PASS", alias="NEO4J_PASSWORD")

  cors_origins: list[str] = Field(
    default=["http://localhost:3000", "http://localhost:5173"],
    description="Allowed origins for CORS",
  )

  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    extra = "ignore"


settings = Settings()
