from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api
from atguigu.task.action.customer.city_mapping import resolve_area_id


class ActionSearchScenic(Action):
    name = "action_search_scenic"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        area_id = resolve_area_id(slots.get("areaId"))
        travel_date = slots.get("travelDate", "")

        if area_id is None:
            return ActionResult(messages=[BotMessage(text="没有找到这个城市的信息，请告诉我具体的城市名称。")])

        result = await travel_api.search_scenic_spots(
            areaId=area_id, travelDate=travel_date,
            scenicTypeCodes=slots.get("scenicTypeCodes"),
            ratingCodes=slots.get("ratingCodes"),
            keyword=slots.get("keyword"),
        )

        if result is None:
            return ActionResult(messages=[BotMessage(text="系统暂时繁忙，请稍后再试。")])

        spots = result.get("list", []) if isinstance(result, dict) else []
        if not spots:
            return ActionResult(messages=[BotMessage(text="该日期暂无符合条件的景点，试试其他日期或类型？")])

        state.record_search(
            "scenic_spot",
            [s.get("scenicSpotId") for s in spots if s.get("scenicSpotId") is not None],
            {"travelDate": travel_date},
        )

        lines = [f"为你找到 {len(spots)} 个景点："]
        for i, s in enumerate(spots[:5], 1):
            name = s.get("scenicName", "未知")
            stype = s.get("scenicTypeCode", "")
            rating = s.get("ratingCode", "")
            price = s.get("minSalePriceAmount", "")
            price_text = f"¥{int(price)}起" if price else "价格待询"
            lines.append(f"{i}. {name} [{rating}/{stype}] {price_text}")

        lines.append("\n你可以告诉我序号或景点名称，查看详细信息和票种。")
        return ActionResult(messages=[BotMessage(text="\n".join(lines))])
