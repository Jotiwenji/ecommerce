from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api
from atguigu.task.action.customer.city_mapping import resolve_area_id


TRANSPORT_TYPE_MAP = {
    "flight": ("机票", travel_api.search_flights, travel_api.get_flight_detail),
    "train": ("火车票", travel_api.search_trains, travel_api.get_train_detail),
    "bus": ("汽车票", travel_api.search_buses, travel_api.get_bus_detail),
}


class ActionSearchTransport(Action):
    name = "action_search_transport"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        transport_type = slots.get("transportType", "flight")
        departure_id = resolve_area_id(slots.get("departureAreaId"))
        arrival_id = resolve_area_id(slots.get("arrivalAreaId"))
        departure_date = slots.get("departureDate", "")
        detail_id = slots.get("departureId")
        if not detail_id and slots.get("transportIndex"):
            detail_id = state.resolve_ordinal(transport_type, slots.get("transportIndex"))

        if transport_type not in TRANSPORT_TYPE_MAP:
            return ActionResult(messages=[BotMessage(text="你想查机票、火车票还是汽车票？")])

        label, search_fn, detail_fn = TRANSPORT_TYPE_MAP[transport_type]

        if detail_id:
            try:
                detail = await detail_fn(int(detail_id))
            except (ValueError, TypeError):
                return ActionResult(messages=[BotMessage(text="班次编号格式有误，请重新告诉我。")])
            if detail is None:
                return ActionResult(messages=[BotMessage(text="暂时无法查到该班次详情，请稍后再试。")])
            return ActionResult(messages=[BotMessage(text=self._format_detail(detail, label))])

        if departure_id is None or arrival_id is None:
            return ActionResult(messages=[BotMessage(text="请告诉我出发城市和到达城市。")])

        kwargs = {"departureAreaId": departure_id, "arrivalAreaId": arrival_id, "departureDate": departure_date}
        if transport_type == "flight":
            kwargs["cabinClassCodes"] = slots.get("cabinClassCodes")
            kwargs["airlineCodes"] = slots.get("airlineCodes")
        elif transport_type == "train":
            kwargs["seatClassCodes"] = slots.get("seatClassCodes")
            kwargs["trainNo"] = slots.get("trainNo")
        elif transport_type == "bus":
            kwargs["routeName"] = slots.get("routeName")

        result = await search_fn(**kwargs)

        if result is None:
            return ActionResult(messages=[BotMessage(text="系统暂时繁忙，请稍后再试。")])

        items = result.get("list", []) if isinstance(result, dict) else []
        if not items:
            return ActionResult(messages=[BotMessage(text=f"没有找到符合条件的{label}，试试换个日期？")])

        state.record_search(
            transport_type,
            [it.get("departureId") for it in items if it.get("departureId") is not None],
            {"departureDate": departure_date},
        )

        lines = [f"为你找到 {len(items)} 个{label}班次："]
        for i, item in enumerate(items[:5], 1):
            code = item.get("flightNo") or item.get("trainNo") or item.get("routeName") or "未知"
            dep_time = item.get("departureTime", "")
            arr_time = item.get("arrivalTime", "")
            dep_hub = item.get("departureHubName", "")
            arr_hub = item.get("arrivalHubName", "")
            price = item.get("minSalePriceAmount") or item.get("salePriceAmount", "")
            price_text = f"¥{int(price)}起" if price else "价格待询"
            lines.append(f"{i}. {code} {dep_hub}→{arr_hub} {dep_time}-{arr_time} {price_text}")

        lines.append("\n你可以告诉我序号，查看详细舱位/席别信息。")
        return ActionResult(messages=[BotMessage(text="\n".join(lines))])

    @staticmethod
    def _format_detail(detail: dict, label: str) -> str:
        code = detail.get("flightNo") or detail.get("trainNo") or detail.get("routeName") or "未知"
        lines = [f"【{code} {label}详情】"]
        lines.append(f"出发：{detail.get('departureHubName', '')} {detail.get('departureTime', '')}")
        lines.append(f"到达：{detail.get('arrivalHubName', '')} {detail.get('arrivalTime', '')}")
        if detail.get("durationMinutes"):
            lines.append(f"时长：{detail['durationMinutes']}分钟")

        cabins = detail.get("cabins") or detail.get("seats") or []
        if cabins:
            lines.append("\n可选舱位/席别：")
            for c in cabins:
                cls_code = c.get("cabinClassCode") or c.get("seatClassCode", "")
                price = c.get("salePriceAmount", "")
                stock = c.get("availableInventory", "")
                price_text = f"¥{int(price)}" if price else "价格待询"
                stock_text = f"余票{stock}" if stock else ""
                lines.append(f"  - {cls_code} {price_text} {stock_text}")

        return "\n".join(lines)
