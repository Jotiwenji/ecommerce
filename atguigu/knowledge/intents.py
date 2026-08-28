from dataclasses import dataclass


@dataclass(slots=True)
class KnowledgeIntent:
    id: str
    description: str
    provider_ids: list[str]
    requires_object: str | None = None


KNOWLEDGE_INTENTS: dict[str, KnowledgeIntent] = {
    "faq_hotel_policy": KnowledgeIntent(
        id="faq_hotel_policy", description="酒店预订政策咨询（入住/退房/加床/取消规则）",
        provider_ids=["faq.hotel_policy"],
    ),
    "faq_scenic_policy": KnowledgeIntent(
        id="faq_scenic_policy", description="景点门票政策咨询（开放时间/儿童票/入园须知）",
        provider_ids=["faq.scenic_policy"],
    ),
    "faq_flight_policy": KnowledgeIntent(
        id="faq_flight_policy", description="机票退改签政策咨询",
        provider_ids=["faq.flight_policy"],
    ),
    "faq_train_policy": KnowledgeIntent(
        id="faq_train_policy", description="火车票退改/改签规则咨询",
        provider_ids=["faq.train_policy"],
    ),
    "faq_payment": KnowledgeIntent(
        id="faq_payment", description="支付与发票咨询",
        provider_ids=["faq.payment"],
    ),
    "faq_document": KnowledgeIntent(
        id="faq_document", description="出行人证件要求咨询",
        provider_ids=["faq.document"],
    ),
    "faq_general": KnowledgeIntent(
        id="faq_general", description="通用旅游FAQ",
        provider_ids=["faq.general"],
    ),
}
