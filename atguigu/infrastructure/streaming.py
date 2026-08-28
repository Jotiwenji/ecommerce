from dataclasses import dataclass, field
from typing import Any


@dataclass
class StreamEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"type": self.type, "data": self.data}


ACTION_PROGRESS_MAP = {
    "action_search_hotels": "正在查询酒店...",
    "action_get_hotel_detail": "正在获取酒店详情...",
    "action_search_scenic": "正在查询景点...",
    "action_get_scenic_detail": "正在获取景点详情...",
    "action_search_transport": "正在查询交通班次...",
    "action_query_orders": "正在查询订单...",
    "action_get_order_detail": "正在获取订单详情...",
    "action_query_itinerary": "正在查询行程...",
    "action_validate_refund_order": "正在验证订单退款资格...",
    "action_submit_refund": "正在提交退款申请...",
    "action_create_work_order": "正在创建工单...",
}


def stage_event(text: str) -> StreamEvent:
    return StreamEvent(type="stage", data={"text": text})


def progress_event(action_name: str) -> StreamEvent | None:
    text = ACTION_PROGRESS_MAP.get(action_name)
    if text:
        return StreamEvent(type="progress", data={"text": text})
    return None


def delta_event(token: str) -> StreamEvent:
    return StreamEvent(type="delta", data={"token": token})


def message_event(text: str, obj: dict | None = None) -> StreamEvent:
    data: dict[str, Any] = {"text": text}
    if obj:
        data["object"] = obj
    return StreamEvent(type="message", data=data)


def error_event(text: str) -> StreamEvent:
    return StreamEvent(type="error", data={"text": text})


def done_event() -> StreamEvent:
    return StreamEvent(type="done", data={})
