from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class ActionRecommendProduct(Action):
    name = "action_recommend_product"

    async def run(self, action_kwargs: dict, state: DialogueState) -> ActionResult:
        return ActionResult(messages=[BotMessage(
            text="目前推荐功能还在开发中。你可以告诉我目的地和日期，我帮你查询酒店、景点或交通信息。"
        )])
