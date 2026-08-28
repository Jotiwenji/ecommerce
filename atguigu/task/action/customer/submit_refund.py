from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.travel_client import travel_api


async def _resolve_order_id(state: DialogueState, raw) -> int | None:
    """把 orderId 槽位（可能是数字ID / ORD单号 / 序号）解析为真实数字 orderId。"""
    if raw is None:
        return None
    raw_str = str(raw).strip()
    if raw_str.isdigit():
        return int(raw_str)
    params = state.get_search_params("order")
    order_no_map = params.get("orderNoMap", {})
    if raw_str in order_no_map:
        return int(order_no_map[raw_str])
    lookup = await travel_api.query_orders(sender_id=state.sender_id, pageSize=50)
    for o in (lookup.get("list", []) if isinstance(lookup, dict) else []):
        if o.get("orderNo") == raw_str and o.get("orderId") is not None:
            return int(o.get("orderId"))
    return None


class ActionValidateRefundOrder(Action):
    name = "action_validate_refund_order"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        sender_id = state.sender_id

        order_id = await _resolve_order_id(state, slots.get("orderId"))

        if order_id is None:
            return ActionResult(slots={"refund_error": "未找到该订单，请确认订单号是否正确。"})

        result = await travel_api.get_order_detail(order_id, sender_id=sender_id)

        if result is None or (isinstance(result, dict) and result.get("_error")):
            return ActionResult(slots={"refund_error": "未找到该订单，请确认订单号是否正确。"})

        status = result.get("statusCode", "")
        if status not in ("paid", "in_progress", "finished"):
            return ActionResult(slots={"refund_error": "该订单当前状态不支持退款，仅已支付/进行中的订单可申请退款。"})

        items = result.get("items", [])
        if not items:
            return ActionResult(slots={"refund_error": "该订单没有可退款的商品明细。"})

        first_item = items[0]
        item_id = first_item.get("orderItemId")
        sale_amount = first_item.get("saleAmount") or 0
        refunded_amount = first_item.get("refundedAmount") or 0
        refundable = float(sale_amount) - float(refunded_amount)

        if refundable <= 0:
            return ActionResult(slots={"refund_error": "该订单已无可退金额。"})

        return ActionResult(slots={
            "itemId": str(item_id),
            "refundable_amount": str(int(refundable)),
            "refund_error": None,
        })


class ActionSubmitRefund(Action):
    name = "action_submit_refund"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        slots = state.activated_task.slots if state.activated_task else {}
        item_id = slots.get("itemId")
        requested_amount = slots.get("requestedAmount")
        reason = slots.get("reason", "")
        sender_id = state.sender_id

        order_id = await _resolve_order_id(state, slots.get("orderId"))

        if not all([order_id, item_id, requested_amount]):
            return ActionResult(messages=[BotMessage(text="退款信息不完整，请重新提供。")])

        try:
            result = await travel_api.create_refund_request(
                orderId=int(order_id),
                itemId=int(item_id),
                requestedAmount=float(requested_amount),
                reason=reason,
                sender_id=sender_id,
            )
        except Exception:
            return ActionResult(messages=[BotMessage(text="退款申请提交失败，请稍后再试。")])

        if isinstance(result, dict) and result.get("_error"):
            msg = result.get("_message", "")
            low = msg.lower()
            if "超过" in msg or "剩余可退" in msg or "remaining" in low or "amount" in low:
                return ActionResult(messages=[BotMessage(text="申请金额超过该订单剩余可退金额，请重新输入退款金额。")])
            if "进行中" in msg or "存在" in msg or "已有" in msg or "in-flight" in low or "pending" in low or "exist" in low:
                return ActionResult(messages=[BotMessage(text="该订单已有进行中的退款申请，请勿重复提交。")])
            return ActionResult(messages=[BotMessage(text=f"退款申请提交失败：{msg}")])

        refund_no = result.get("refundRequestNo", "") if isinstance(result, dict) else ""
        return ActionResult(messages=[BotMessage(
            text=f"退款申请已提交成功，申请单号：{refund_no}。我们会尽快审核处理。"
        )])
