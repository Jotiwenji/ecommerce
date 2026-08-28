import asyncio

from atguigu.domain.messages import UserMessage, ProcessResult, ChatHistoryMessage
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.history.builder import ChatHistoryBuilder
from atguigu.infrastructure.streaming import StreamEvent, done_event, error_event
from atguigu.repository.dialogue_repository import DialogueRepository


class DialogueService:

    def __init__(self,
                 engine: DialogueEngine,
                 repository: DialogueRepository
                 ):
        self._engine = engine
        self._repository = repository

    async def process_message(self, user_message: UserMessage) -> ProcessResult:
        """
        每一轮对话都会做数据库读写操作和引擎的计算
        Args:
            user_message:

        Returns:

        """

        # 1. 从数据库中读取最新的状态
        dialogue_state = await self._repository.load_state(user_message.sender_id)

        # 2. 调用引擎做各种逻辑处理(调用LLM 进行路由分析、推进流程...)
        process_result = await self._engine.process_message(user_message, dialogue_state)

        # 3. 将引擎层修改后的最新状态存储到数据库中
        await self._repository.save_state(user_message.sender_id, dialogue_state)

        # 4. 返回引擎层处理后的结果(机器人回复)
        return process_result

    async def reset_state(self, sender_id: str) -> None:
        """重置该用户的运行时对话状态：清空卡住的活跃/挂起流程，但保留历史 session。"""
        dialogue_state = await self._repository.load_state(sender_id)
        dialogue_state.reset_runtime_state_for_new_session()
        await self._repository.save_state(sender_id, dialogue_state)

    async def process_message_stream(self, user_message: UserMessage):
        queue: asyncio.Queue = asyncio.Queue()

        async def _run():
            try:
                dialogue_state = await self._repository.load_state(user_message.sender_id)
                process_result = await self._engine.process_message(
                    user_message, dialogue_state,
                    event_sink=lambda evt: queue.put_nowait(evt)
                )
                await self._repository.save_state(user_message.sender_id, dialogue_state)

                from atguigu.infrastructure.streaming import message_event
                for bot_message in process_result.messages:
                    obj_dict = None
                    if bot_message.object is not None:
                        obj_dict = {
                            "id": bot_message.object.id,
                            "type": bot_message.object.type,
                            "title": bot_message.object.title,
                            "attributes": bot_message.object.attributes,
                        }
                    await queue.put(message_event(bot_message.text, obj_dict))
            except Exception as e:
                await queue.put(error_event(str(e)))
            finally:
                await queue.put(done_event())

        task = asyncio.create_task(_run())

        while True:
            event: StreamEvent = await queue.get()
            yield event
            if event.type == "done":
                break

        await task

    async def get_chat_history(self, sender_id: str) -> list[ChatHistoryMessage]:
        # 1.  查询当前用户对应的整个对话状态
        state = await self._repository.load_state(sender_id)

        # 2. 获取当前用户对话状态的sessions
        final_chat_history = []
        for session in state.sessions:

            for turn in session.turns:
                user_message = turn.user_message

                user_chat_message = ChatHistoryBuilder.build_chat_history(session.session_id, "user", user_message.text,
                                                                          user_message.object)

                final_chat_history.append(user_chat_message)

                bot_messages = turn.bot_messages

                for bot_message in bot_messages:
                    bot_chat_message = ChatHistoryBuilder.build_chat_history(session.session_id,
                                                                             "bot",
                                                                             bot_message.text,
                                                                             bot_message.object)

                    final_chat_history.append(bot_chat_message)

        return final_chat_history