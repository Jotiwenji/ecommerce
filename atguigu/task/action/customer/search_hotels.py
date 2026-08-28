from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api
from atguigu.task.action.customer.city_mapping import resolve_area_id


class ActionSearchHotels(Action):
    name = "action_search_hotels"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        area_id = resolve_area_id(slots.get("areaId"))
        check_in = slots.get("checkInDate", "")
        check_out = slots.get("checkOutDate", "")

        if area_id is None:
            return ActionResult(messages=[BotMessage(text="没有找到这个城市的信息，请告诉我具体的城市名称。")])

        result = await travel_api.search_hotels(
            areaId=area_id, checkInDate=check_in, checkOutDate=check_out,
            starRatingCodes=slots.get("starRatingCodes"),
            hotelTypeCodes=slots.get("hotelTypeCodes"),
            keyword=slots.get("keyword"),
        )

        if result is None:
            return ActionResult(messages=[BotMessage(text="系统暂时繁忙，请稍后再试。")])

        hotels = result.get("list", []) if isinstance(result, dict) else []
        if not hotels:
            return ActionResult(messages=[BotMessage(text="该日期段没有找到符合条件的酒店，你可以换个日期或放宽筛选条件试试。")])

        state.record_search(
            "hotel",
            [h.get("hotelId") for h in hotels if h.get("hotelId") is not None],
            {"checkInDate": check_in, "checkOutDate": check_out},
        )

        lines = [f"为你找到 {len(hotels)} 家酒店："]
        for i, h in enumerate(hotels[:5], 1):
            name = h.get("hotelName", "未知")
            star = h.get("starRatingCode", "")
            price = h.get("minSalePriceAmount", "")
            addr = h.get("address", "")
            star_text = f"{'⭐' * int(star)} " if star else ""
            price_text = f"¥{int(price)}起" if price else "价格待询"
            lines.append(f"{i}. {star_text}{name} {price_text} {addr}")

        lines.append("\n你可以告诉我序号或酒店名称，查看详细信息和房型。")
        return ActionResult(messages=[BotMessage(text="\n".join(lines))])
