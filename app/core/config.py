import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    zhipu_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Embedding
    bailian_api_key: str = ""
    bailian_embedding_model: str = "text-embedding-v4"

    # 默认模型
    default_llm_model: str = "zhipu"

    # 搜索
    tavily_api_key: str = ""
    default_search_engine: str = "tavily"

    # JWT
    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    # 数据库
    database_url: str = "data/sqlite/shuangti.db"

    # ChromaDB
    chroma_persist_dir: str = "data/chroma"

    # 服务
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
