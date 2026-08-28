"""
LLM 流式调用工具：
1. 过滤推理模型的 <think>...</think> 内容
2. 支持 event_sink 逐 token 推送 delta 事件
3. 提供 text / json 两种流式调用模式
"""
import json as _json
import re
from typing import Any, Callable

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from atguigu.infrastructure.llm import llm_client


def _strip_thinking(text: str) -> str:
    return re.sub(r'<think>[\s\S]*?</think>', '', text)


async def stream_llm_text(prompt_template: PromptTemplate,
                          prompt_inputs: dict[str, Any],
                          event_sink: Callable | None = None) -> str:
    """流式调用 LLM，返回纯文本。逐 token 通过 event_sink 推送 delta 事件。"""
    from atguigu.infrastructure.streaming import delta_event

    formatted = prompt_template.invoke(prompt_inputs)

    parts: list[str] = []
    in_think = False

    async for chunk in llm_client.astream(formatted):
        content = chunk.content if hasattr(chunk, 'content') else str(chunk)
        if not content:
            continue

        if '<think>' in content:
            in_think = True
            content = content.split('<think>')[0]

        if in_think:
            if '</think>' in content:
                in_think = False
                content = content.split('</think>')[-1]
            else:
                continue

        content = _strip_thinking(content)
        if content:
            parts.append(content)
            if event_sink is not None:
                event_sink(delta_event(content))

    return ''.join(parts)


async def stream_llm_json(prompt_template: PromptTemplate,
                          prompt_inputs: dict[str, Any],
                          event_sink: Callable | None = None) -> dict:
    """流式调用 LLM，返回 JSON dict。thinking 内容被过滤，不进入解析。"""
    formatted = prompt_template.invoke(prompt_inputs)

    parts: list[str] = []
    in_think = False

    async for chunk in llm_client.astream(formatted):
        content = chunk.content if hasattr(chunk, 'content') else str(chunk)
        if not content:
            continue

        if '<think>' in content:
            in_think = True
            content = content.split('<think>')[0]

        if in_think:
            if '</think>' in content:
                in_think = False
                content = content.split('</think>')[-1]
            else:
                continue

        content = _strip_thinking(content)
        if content:
            parts.append(content)

    raw = ''.join(parts)
    parser = JsonOutputParser()
    return parser.parse(raw)
