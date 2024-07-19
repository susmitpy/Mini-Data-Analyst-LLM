from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage


class Node(Enum):
    AGENT = "agent"
    EXECUTE = "execute"

@dataclass
class AgentState:
    messages: Annotated[list[AnyMessage], add_messages]
    prev_results: dict[str, Any]
    human_stop: bool
    show_last_two_messages: bool
