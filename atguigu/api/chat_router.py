import json
import uuid
from dataclasses import dataclass
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from atguigu.api.schemas import ChatRequest, ChatResponse, ChatBotMessage, ChatObject, ChatHistoryResponse
from atguigu.domain.messages import UserMessage, ProcessResult, MessageType, FocusedObject
from atguigu.api.dependencies import DialogueServiceDep
from atguigu.task.action.customer.travel_client import travel_api

router = APIRouter()


@dataclass
class User:
    name: str
    age: int
    address: str


@router.get("/hello", response_model=User)
def hello():
    """
    路由函数返回的数据模型自动会被fastapi(springmvc[springboot])进行序列化
    响应：User对象-----fastapi-----"{}" json格式的字符串：是个字符串  "abc"
    请求：前端发送请求（请求数据）---->请求体中(application/json)---json格式的字符串--- fastapi-----对象（定义这个对象） 反序列化
    "{"name":"zs","age":18,"address":"sz"}"----User
    :return:

    指定response_model之后
    1. 可以通过swagger_ui 看到接口的详细响应信息，不只是有状态嘛，还有schema约束（响应字段、字段类型）
    2. 过滤字段
    3. 字段类型校验以及类型转换
    4. 序列化(加不加都能序列化)
    """
    return {
        "name": "zs",
        "age": "abc",
        "address": "sz",
    }


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest,
                        service: DialogueServiceDep):
    """
    :param chat_request:
    :return:
    """
    # 1. 接口数据模型转换成领域数据模型
    user_message = _build_user_message(chat_request)

    # 2. 调用service处理消息（领域数据模型）--- 结果：领域数据模型
    process_result: ProcessResult = await service.process_message(user_message)

    # 3. 将结果领域数据模型转换成接口数据模型
    chat_response = _build_chat_response(process_result)

    # 4. 返回接口数据模型
    return chat_response


@router.post("/api/chat/stream")
async def chat_stream_endpoint(chat_request: ChatRequest,
                               service: DialogueServiceDep):
    user_message = _build_user_message(chat_request)

    async def event_generator():
        async for stream_event in service.process_message_stream(user_message):
            yield f"data: {json.dumps(stream_event.to_dict(), ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _build_user_message(chat_request: ChatRequest) -> UserMessage:
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id=str(uuid.uuid4()),
        type=MessageType.OBJECT if chat_request.object is not None else MessageType.TEXT,
        text=chat_request.text,
        object=FocusedObject(
            id=chat_request.object.id,
            type=chat_request.object.type,
            title=chat_request.object.title,
            attributes=chat_request.object.attributes
        ) if chat_request.object is not None else None
    )


def _build_chat_response(process_result: ProcessResult) -> ChatResponse:
    return ChatResponse(
        message_id=process_result.message_id,
        messages=[
            ChatBotMessage(text=bot_message.text,
                           object=ChatObject(
                               id=bot_message.object.id,
                               type=bot_message.object.type,
                               title=bot_message.object.title,
                               attributes=bot_message.object.attributes
                           ) if bot_message.object is not None else None
                           )
            for bot_message in process_result.messages
        ]
    )


@router.get("/api/chat/history", response_model=ChatHistoryResponse)
async def chat_history_endpoint(sender_id: str,
                                service: DialogueServiceDep):
    chat_history_messages = await service.get_chat_history(sender_id)

    return ChatHistoryResponse(sender_id=sender_id, messages=chat_history_messages)


@router.post("/api/chat/reset")
async def chat_reset_endpoint(service: DialogueServiceDep,
                              sender_id: str = Query(..., description="数字用户ID")):
    """清空该用户卡住的活跃流程（保留历史），供前端'新会话'按钮调用。"""
    await service.reset_state(sender_id)
    return {"sender_id": sender_id, "reset": True}


@router.get("/api/orders")
async def orders_proxy_endpoint(sender_id: str = Query(..., description="数字用户ID"),
                                page_size: int = Query(20, alias="pageSize", ge=1, le=50)):
    """代理转发中台订单列表，供前端'我的订单'侧栏点击发送卡片。"""
    result = await travel_api.query_orders(sender_id=sender_id, pageSize=page_size)
    orders = result.get("list", []) if isinstance(result, dict) else []
    return {
        "sender_id": sender_id,
        "orders": [
            {
                "orderId": o.get("orderId"),
                "orderNo": o.get("orderNo"),
                "orderTypeCode": o.get("orderTypeCode"),
                "statusCode": o.get("statusCode"),
                "payableAmount": o.get("payableAmount"),
                "createdAt": o.get("createdAt"),
            }
            for o in orders
        ]
    }
