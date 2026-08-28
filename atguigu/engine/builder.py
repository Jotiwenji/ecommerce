from pathlib import Path

from atguigu.chitchat.responder import ChitChatResponder
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.knowledge.providers.register import ProviderRegister
from atguigu.knowledge.responder import KnowledgeResponder
from atguigu.plan.planner import TurnPlanner
from atguigu.plan.validator import TurnPlanValidator
from atguigu.clarify.responder import ClarifyResponder
from atguigu.task.action.buidler import build_action_runner
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flows.executor import FlowExecutor
from atguigu.task.handler import TaskHandler
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.chitchat.handler import ChitChatHandler
from atguigu.task.flows.loader import FlowLoader
from atguigu.knowledge.intents import KNOWLEDGE_INTENTS
from atguigu.knowledge.providers.knowledge import TravelFAQProvider
from atguigu.knowledge.faq_content import (
    FAQ_HOTEL_POLICY, FAQ_SCENIC_POLICY, FAQ_FLIGHT_POLICY,
    FAQ_TRAIN_POLICY, FAQ_PAYMENT, FAQ_DOCUMENT, FAQ_GENERAL,
)

PROJECT_ROOT_DIR = Path(__file__).resolve().parents[2]

FLOW_CONFIG_DIR = PROJECT_ROOT_DIR / "flow_config"

FLOW_CONFIGS = ["system_flows.yml", "user_flows.yml"]


def build_dialogue_engine():
    flows_list = FlowLoader().load_multi_yaml([FLOW_CONFIG_DIR / flow_config for flow_config in FLOW_CONFIGS])

    return DialogueEngine(
        turn_planner=TurnPlanner(),
        turn_plan_validator=TurnPlanValidator(),
        clarify_responder=ClarifyResponder(),
        task_handler=TaskHandler(
            flows_list=flows_list,
            command_processor=CommandProcessor(),
            flow_executor=FlowExecutor(),
            action_runner=build_action_runner()
        ),
        knowledge_handler=KnowledgeHandler(knowledge_intents=KNOWLEDGE_INTENTS,
                                           knowledge_responder=KnowledgeResponder(),
                                           providers_register= ProviderRegister(providers=[
                                               TravelFAQProvider("faq.hotel_policy", FAQ_HOTEL_POLICY),
                                               TravelFAQProvider("faq.scenic_policy", FAQ_SCENIC_POLICY),
                                               TravelFAQProvider("faq.flight_policy", FAQ_FLIGHT_POLICY),
                                               TravelFAQProvider("faq.train_policy", FAQ_TRAIN_POLICY),
                                               TravelFAQProvider("faq.payment", FAQ_PAYMENT),
                                               TravelFAQProvider("faq.document", FAQ_DOCUMENT),
                                               TravelFAQProvider("faq.general", FAQ_GENERAL),
                                           ])
                                           ),
        chitchat_handler=ChitChatHandler(chat_responder=ChitChatResponder())
    )
