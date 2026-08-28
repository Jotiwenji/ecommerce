from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from atguigu.history.builder import ChatHistoryBuilder
from atguigu.infrastructure.llm import llm_client
from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.prompt.loader import load_prompt_template


class ChitChatResponder:

    async def respond_chat(self,
                           chat: str,
                           state: DialogueState,
                           event_sink=None) -> list[BotMessage]:
        # 1. 加载闲聊的提示词内容
        prompt_template_str = load_prompt_template("chitchat_respond")

        # 2. 实例化提示词模版对象
        prompt_template = PromptTemplate.from_template(template=prompt_template_str, template_format="jinja2")

        # 3. 流式调用LLM（自动过滤think内容）
        from atguigu.infrastructure.llm_streaming import stream_llm_text
        result = await stream_llm_text(prompt_template, {
            "user_message": chat,
            "history": ChatHistoryBuilder.build(state.current_session().turns[-10:])
        }, event_sink=event_sink)

        return [BotMessage(text=result)]
