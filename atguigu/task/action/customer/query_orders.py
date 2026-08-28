from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api


class ActionQueryOrders(Action):
    name = "action_query_orders"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        sender_id = state.sender_id

        result = await travel_api.query_orders(
            sender_id=sender_id,
            statusCode=slots.get("statusCode"),
            orderTypeCode=slots.get("orderTypeCode"),
        )

        if result is None:
            return ActionResult(messages=[BotMessage(text="系统暂时繁忙，请稍后再试。")])

        orders = result.get("list", []) if isinstance(result, dict) else []
        if not orders:
            return ActionResult(messages=[BotMessage(text="你当前没有符合条件的订单。")])

        ordered_ids = [o.get("orderId") for o in orders if o.get("orderId") is not None]
        order_no_map = {o.get("orderNo"): o.get("orderId") for o in orders
                        if o.get("orderNo") and o.get("orderId") is not None}
        state.record_search("order", ordered_ids, {"orderNoMap": order_no_map})

        status_map = {
            "pending_payment": "待支付", "paid": "已支付",
            "in_progress": "进行中", "finished": "已结束", "cancelled": "已取消",
        }
        type_map = {
            "hotel_room": "酒店", "scenic_ticket": "景点",
            "flight_cabin": "机票", "train_seat": "火车票",
            "bus_seat": "汽车票", "transfer_service": "接送",
        }

        lines = [f"你最近有 {len(orders)} 个订单："]
        for i, o in enumerate(orders[:5], 1):
            order_no = o.get("orderNo", "")
            otype = type_map.get(o.get("orderTypeCode", ""), "未知")
            status = status_map.get(o.get("statusCode", ""), "未知")
            amount = o.get("payableAmount", "")
            amount_text = f"¥{amount}" if amount else ""
            created = o.get("createdAt", "")[:10] if o.get("createdAt") else ""
            lines.append(f"{i}. [{otype}] {order_no} {status} {amount_text} {created}")

        lines.append("\n你可以告诉我订单号，查看详细信息。")
        return ActionResult(messages=[BotMessage(text="\n".join(lines))])
