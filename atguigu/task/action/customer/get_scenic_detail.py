import asyncio

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api


async def _none_coro():
    return None


class ActionGetScenicDetail(Action):
    name = "action_get_scenic_detail"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        params = state.get_search_params("scenic_spot")

        scenic_id = slots.get("scenicSpotId")
        if not scenic_id and slots.get("scenicIndex"):
            scenic_id = state.resolve_ordinal("scenic_spot", slots.get("scenicIndex"))
        travel_date = slots.get("travelDate") or params.get("travelDate", "")

        if not scenic_id:
            return ActionResult(messages=[BotMessage(text="请告诉我你想查看第几个景点。")])

        try:
            scenic_id = int(scenic_id)
        except (ValueError, TypeError):
            return ActionResult(messages=[BotMessage(text="景点编号格式有误，请重新告诉我。")])

        detail_task = travel_api.get_scenic_detail(scenic_id)
        tickets_task = travel_api.get_ticket_types(scenic_id, travel_date) if travel_date else _none_coro()
        detail, tickets = await asyncio.gather(detail_task, tickets_task)

        if detail is None:
            return ActionResult(messages=[BotMessage(text="暂时无法查到该景点信息，请稍后再试。")])

        lines = [f"【{detail.get('scenicName', '未知景点')}】"]
        lines.append(f"地址：{detail.get('address', '')}")
        if detail.get("ratingCode"):
            lines.append(f"等级：{detail['ratingCode']}")
        if detail.get("openTime"):
            lines.append(f"开放时间：{detail['openTime']} - {detail.get('closeTime', '')}")
        if detail.get("tagPayload"):
            tags = [t.get("tagName", "") if isinstance(t, dict) else str(t)
                    for t in detail["tagPayload"]]
            tags = [t for t in tags if t]
            if tags:
                lines.append(f"特色：{', '.join(tags[:6])}")

        ticket_list = tickets.get("list", []) if tickets and isinstance(tickets, dict) else []
        if ticket_list:
            lines.append("\n票种与价格：")
            for t in ticket_list[:5]:
                tname = t.get("ticketTypeName", "未知票种")
                price = t.get("salePriceAmount", "")
                stock = t.get("availableTicketCount", "")
                price_text = f"¥{int(price)}" if price else "价格待询"
                stock_text = f"剩余{stock}张" if stock else ""
                lines.append(f"  - {tname} {price_text} {stock_text}")

        return ActionResult(messages=[BotMessage(text="\n".join(lines))])
