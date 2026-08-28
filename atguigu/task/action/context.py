"""
Action 执行上下文：通过 contextvars 传递 event_sink 等运行时上下文，
避免修改所有 Action.run() 签名。
"""
import contextvars

action_event_sink: contextvars.ContextVar = contextvars.ContextVar('action_event_sink', default=None)
