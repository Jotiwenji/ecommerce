from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api


class ActionQueryItinerary(Action):
    name = "action_query_itinerary"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        sender_id = state.sender_id

        paid, in_progress = await __import__("asyncio").gather(
            travel_api.query_orders(sender_id=sender_id, statusCode="paid"),
            travel_api.query_orders(sender_id=sender_id, statusCode="in_progress"),
        )

        all_orders = []
        for result in [paid, in_progress]:
            if result and isinstance(result, dict):
                all_orders.extend(result.get("list", []))

        if not all_orders:
            return ActionResult(messages=[BotMessage(text="你当前没有待出行的订单。")])

        type_map = {
            "hotel_room": "酒店", "scenic_ticket": "景点",
            "flight_cabin": "机票", "train_seat": "火车票",
            "bus_seat": "汽车票", "transfer_service": "接送",
        }

        lines = ["你的行程安排："]
        for o in all_orders[:5]:
            otype = type_map.get(o.get("orderTypeCode", ""), "未知")
            order_no = o.get("orderNo", "")
            amount = o.get("payableAmount", "")
            lines.append(f"  - [{otype}] 订单 {order_no} ¥{amount}")

        lines.append("\n你可以告诉我订单号，查看详细的行程信息。")
        return ActionResult(messages=[BotMessage(text="\n".join(lines))])
