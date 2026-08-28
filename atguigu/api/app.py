from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from atguigu.api import chat_router
from atguigu.infrastructure.database import init_db_engine, dispose_db_engine
from atguigu.infrastructure.client import init_http_client, dispose_http_client
from atguigu.infrastructure.work_order_database import init_work_order_db, dispose_work_order_db


async def lifespan(_: FastAPI):
    """
    生命周期的lifespan函数一定要接收fastapi实例，哪怕函数内不用也要写。
    Args:
        fastapi:

    Returns:

    """
    # 应用启动
    print("应用启动期间回调到...")
    init_db_engine()
    init_http_client()
    await init_work_order_db()

    yield  # 【分割信号/分界线】，为了区分应用启动的时候执行初始化资源 应用关闭执行资源的释放
    print("应用关闭回调到...")
    await dispose_db_engine()
    await dispose_http_client()
    await dispose_work_order_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router.router)

# 挂载前端单页（原生 HTML/JS）到 /ui
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="ui")
