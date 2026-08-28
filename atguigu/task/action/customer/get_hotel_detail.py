import asyncio

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api


async def _none_coro():
    return None


class ActionGetHotelDetail(Action):
    name = "action_get_hotel_detail"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        params = state.get_search_params("hotel")

        hotel_id = slots.get("hotelId")
        if not hotel_id and slots.get("hotelIndex"):
            hotel_id = state.resolve_ordinal("hotel", slots.get("hotelIndex"))
        check_in = slots.get("checkInDate") or params.get("checkInDate", "")
        check_out = slots.get("checkOutDate") or params.get("checkOutDate", "")

        if not hotel_id:
            return ActionResult(messages=[BotMessage(text="请告诉我你想查看第几家酒店。")])

        try:
            hotel_id = int(hotel_id)
        except (ValueError, TypeError):
            return ActionResult(messages=[BotMessage(text="酒店编号格式有误，请重新告诉我。")])

        rooms_task = (travel_api.get_hotel_room_types(hotel_id, check_in, check_out)
                      if check_in and check_out else _none_coro())
        detail, rooms = await asyncio.gather(
            travel_api.get_hotel_detail(hotel_id),
            rooms_task,
        )

        if detail is None:
            return ActionResult(messages=[BotMessage(text="暂时无法查到该酒店信息，请稍后再试。")])

        lines = [f"【{detail.get('hotelName', '未知酒店')}】"]
        lines.append(f"地址：{detail.get('address', '')}")
        lines.append(f"星级：{detail.get('starRatingCode', '')}星")
        if detail.get("checkInTime"):
            lines.append(f"入住时间：{detail['checkInTime']}，退房时间：{detail.get('checkOutTime', '')}")
        if detail.get("facilityTags"):
            lines.append(f"设施：{', '.join(detail['facilityTags'][:6])}")

        room_list = rooms.get("list", []) if rooms and isinstance(rooms, dict) else []
        if room_list:
            lines.append("\n房型与价格：")
            for r in room_list[:5]:
                rname = r.get("roomTypeName", "未知房型")
                price = r.get("firstNightSalePriceAmount", "")
                stock = r.get("availableRoomCount", "")
                price_text = f"¥{int(price)}/晚" if price else "价格待询"
                stock_text = f"剩余{stock}间" if stock else ""
                lines.append(f"  - {rname} {price_text} {stock_text}")

        return ActionResult(messages=[BotMessage(text="\n".join(lines))])
