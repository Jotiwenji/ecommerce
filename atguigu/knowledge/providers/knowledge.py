from atguigu.domain.state import DialogueState
from atguigu.knowledge.providers.base import Provider, KnowledgeChunk


class TravelFAQProvider(Provider):

    def __init__(self, provider_id: str, content: str):
        self.provider_id = provider_id
        self._content = content

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        return [KnowledgeChunk(content=self._content)]
