from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api


class ActionGetOrderDetail(Action):
    name = "action_get_order_detail"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        sender_id = state.sender_id
        params = state.get_search_params("order")
        order_no_map = params.get("orderNoMap", {})

        raw = slots.get("orderId")
        order_id = None
        if raw is not None:
            raw_str = str(raw).strip()
            if raw_str.isdigit():
                order_id = int(raw_str)
            elif raw_str in order_no_map:
                order_id = order_no_map[raw_str]
        if order_id is None and slots.get("orderIndex"):
            resolved = state.resolve_ordinal("order", slots.get("orderIndex"))
            if resolved is not None:
                order_id = int(resolved)

        # 显式给出 orderNo 但本地缓存无映射时，回查订单列表定位真实 orderId
        if order_id is None and raw is not None and not str(raw).strip().isdigit():
            wanted = str(raw).strip()
            lookup = await travel_api.query_orders(sender_id=sender_id, pageSize=50)
            for o in (lookup.get("list", []) if isinstance(lookup, dict) else []):
                if o.get("orderNo") == wanted and o.get("orderId") is not None:
                    order_id = int(o.get("orderId"))
                    break

        if order_id is None:
            return ActionResult(messages=[BotMessage(text="请告诉我你想查看的订单号。")])

        result = await travel_api.get_order_detail(order_id, sender_id=sender_id)

        if result is None:
            return ActionResult(messages=[BotMessage(text="没有找到该订单，请确认订单号是否正确。")])

        if isinstance(result, dict) and result.get("_error"):
            return ActionResult(messages=[BotMessage(text="没有找到该订单，请确认订单号是否正确。")])

        status_map = {
            "pending_payment": "待支付", "paid": "已支付",
            "in_progress": "进行中", "finished": "已结束", "cancelled": "已取消",
        }
        type_map = {
            "hotel_room": "酒店", "scenic_ticket": "景点",
            "flight_cabin": "机票", "train_seat": "火车票",
            "bus_seat": "汽车票", "transfer_service": "接送",
        }

        lines = [f"【订单详情 {result.get('orderNo', '')}】"]
        lines.append(f"类型：{type_map.get(result.get('orderTypeCode', ''), '未知')}")
        lines.append(f"状态：{status_map.get(result.get('statusCode', ''), '未知')}")
        lines.append(f"商品金额：¥{result.get('goodsAmount', '')}")
        lines.append(f"实付金额：¥{result.get('payableAmount', '')}")
        lines.append(f"下单时间：{result.get('createdAt', '')}")

        items = result.get("items", [])
        if items:
            lines.append("\n商品明细：")
            for item in items:
                name = item.get("productName", "")
                amount = item.get("saleAmount", "")
                traveler = item.get("travelerName", "")
                travel_time = item.get("travelTime", "")
                time_text = f" 出行时间：{travel_time}" if travel_time else ""
                traveler_text = f" 出行人：{traveler}" if traveler else ""
                lines.append(f"  - {name} ¥{amount}{traveler_text}{time_text}")

        payments = result.get("payments", [])
        if payments:
            lines.append("\n支付信息：")
            for p in payments:
                method = p.get("paymentMethodCode", "")
                amount = p.get("amount", "")
                status = p.get("statusCode", "")
                lines.append(f"  - {method} ¥{amount} [{status}]")

        return ActionResult(messages=[BotMessage(text="\n".join(lines))])
