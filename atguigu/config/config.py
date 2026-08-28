from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 读取.env文件
PROJECT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_DIR / ".env"


class Settings(BaseSettings):
    """
    接收.env文件中的环境变量

    LLM_MODEL=qwen-plus
    LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
    LLM_API_KEY=sk-xxx

    TRAVEL_API_BASE_URL=http://127.0.0.1:8000/api/v1
    TRAVEL_API_USER_HEADER=X-User-Id
    TRAVEL_API_DEFAULT_USER_ID=10001

    DATABASE_URL=mysql+aiomysql://root:123321@127.0.0.1:3306/customer_service?charset=utf8mb4
    WORK_ORDER_DATABASE_URL=mysql+aiomysql://root:123321@127.0.0.1:3306/work_orders?charset=utf8mb4

    APP_HOST=0.0.0.0
    APP_PORT=18082
    """

    llm_model: str
    llm_base_url: str
    llm_api_key: str
    travel_api_base_url: str
    travel_api_user_header: str = "X-User-Id"
    travel_api_default_user_id: str = "10001"
    database_url: str
    work_order_database_url: str
    app_host: str
    app_port: int

    # 实例化SettingsConfigDict对象一定要有变量接收  并且变量的名字一定要叫model_config
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding="utf-8",
                                      extra="ignore")  # extra="ignore" 忽略掉.env文件中多余的key_value


settings = Settings()  # type: ignore

if __name__ == '__main__':
    print(settings.llm_base_url)
