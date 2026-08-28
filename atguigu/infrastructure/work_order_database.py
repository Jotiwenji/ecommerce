import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from atguigu.config.config import settings

wo_db_engine: AsyncEngine | None = None
wo_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_work_order_db():
    global wo_db_engine, wo_session_factory

    wo_db_engine = create_async_engine(url=settings.work_order_database_url, echo=True)
    wo_session_factory = async_sessionmaker(wo_db_engine, expire_on_commit=False)

    from atguigu.repository.work_order_record import WorkOrderRecord
    async with wo_db_engine.begin() as conn:
        await conn.run_sync(WorkOrderRecord.metadata.create_all, tables=[WorkOrderRecord.__table__])


async def dispose_work_order_db():
    if wo_db_engine:
        await wo_db_engine.dispose()


if __name__ == "__main__":
    async def _test():
        await init_work_order_db()
        async with wo_session_factory() as session:
            from sqlalchemy import text
            result = await session.execute(text("select 1"))
            print(result.fetchone())
        await dispose_work_order_db()

    asyncio.run(_test())
