import time

from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.repository.work_order_record import WorkOrderRecord


async def create_work_order_record(
    session: AsyncSession,
    sender_id: str,
    ticket_type: str,
    order_id: str,
    description: str,
) -> str:
    work_order_no = f"WO{time.strftime('%Y%m%d%H%M%S')}{int(time.time() * 1000) % 1000:03d}"

    record = WorkOrderRecord(
        work_order_no=work_order_no,
        sender_id=sender_id,
        ticket_type=ticket_type,
        order_id=order_id,
        description=description,
        status="pending",
    )
    session.add(record)
    await session.flush()

    return work_order_no
