from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class ActionCreateWorkOrder(Action):
    name = "action_create_work_order"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        ticket_type = slots.get("ticketType", "")
        order_id = slots.get("orderId", "")
        description = slots.get("problemDescription", "")
        sender_id = state.sender_id

        try:
            from atguigu.infrastructure.work_order_database import wo_session_factory
            from atguigu.repository.work_order_repository import create_work_order_record

            async with wo_session_factory() as session:
                work_order_no = await create_work_order_record(
                    session=session,
                    sender_id=sender_id,
                    ticket_type=ticket_type,
                    order_id=order_id,
                    description=description,
                )
                await session.commit()

            return ActionResult(messages=[BotMessage(
                text=f"工单已创建，编号 {work_order_no}，预计 24 小时内处理。"
            )])
        except Exception:
            return ActionResult(messages=[BotMessage(
                text="工单创建失败，请稍后再试或转接人工客服。"
            )])
