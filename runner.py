from typing import Any, Optional
import pandas as pd
import ast

from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models.ollama import ChatOllama
import re

from langtrace_python_sdk import with_langtrace_root_span, inject_additional_attributes


from models import Node, AgentState
import prompts
class Runner:
    debug_conversation: bool
    debug_final_state: bool
    take_human_consent: bool
    globals_dict: dict[str, Any]
    llm: ChatOllama

    def __init__(self, llm, take_human_consent: bool = False,debug_conversation:bool=False, debug_final_state: bool = False):
        self.llm = llm
        self.debug_conversation = debug_conversation
        self.take_human_consent = take_human_consent
        self.debug_final_state = debug_final_state
        self.globals_dict = {
            "pd": pd
        }
        

    def is_consent_denied(self, state: AgentState, mssg: str) -> tuple[bool, AgentState]:
        """
        Returns True if the user denies consent, False otherwise.
        Also updates the state
        """
        print(mssg)
        if not self.take_human_consent:
            return False, state
        
        if input("Press Enter to continue or 'q' to quit: ").lower() == 'q':
            state.human_stop = True
            return True, state

        return False, state

    def execute_code(self, state: AgentState) -> AgentState:
        """
        EXECUTE
        ```
        {code}
        ```
        text
        """
        message: str = state.messages[-1].content
        try:
            code = re.search(r"EXECUTE\n```(.*)```", message, re.DOTALL).group(1)
        except AttributeError:
            state.messages = state.messages + [HumanMessage(content=prompts.NO_CODE_FOUND)]
            return state

        if code in state.prev_results:
            consent_denied, state = self.is_consent_denied(state, "The code has already been executed")
            if consent_denied:
                return state
            state.messages = state.messages + [HumanMessage(content=prompts.CODE_ALREADY_EXECUTED_WITH_RESULT.format(result=state.prev_results[code]))]
            return state

        consent_denied, state = self.is_consent_denied(state, f"Executing code: {code}")
        if consent_denied:
            return state

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    consent_denied, state = self.is_consent_denied(state, "Imports found, telling model to refactor")
                    if consent_denied:
                        return state
                    state.messages = state.messages + [HumanMessage(content=prompts.IMPORTS_NOT_ALLOWED)]
                    return state
            exec_globals = self.globals_dict.copy()
            exec(code, exec_globals)
            result = exec_globals.get('result', None)
            if result is None:
                state.messages = state.messages + [AIMessage(content=prompts.NO_RESULT_FOUND)]
                return state
            state.prev_results[code] = result
            # Add result to globals dict for next execution
            self.globals_dict['result'] = state.prev_results[code] # if it's a dataframe, it will be passed as a reference thus saving memory
            state.messages = state.messages + [AIMessage(content=prompts.EXECUTION_COMPLETE.format(result=result)), HumanMessage(content="Give final answer END {answer} or execute more code")]
            state.show_last_two_messages = True # So that the user can see the result of the code execution
            return state
        except Exception as e:
            state.messages = state.messages + [AIMessage(content=prompts.ERROR_EXECUTING_CODE.format(e=e))]
            return state
    
    def call_model(self, state: AgentState) -> AgentState:
        messages = state.messages
        last_message = messages[-1]

        if last_message.content.startswith("EXECUTE") and "END" in last_message.content:
            consent_denied, state = self.is_consent_denied(state, "Both execute and end found, telling model to refactor")
            if consent_denied:
                return state
            state.messages = state.messages + [HumanMessage(content=prompts.BOTH_EXECUTE_END)]
            return state
        
        mssg_to_display = f"Calling model with messages: {[m.content for m in messages[-2:]]}" if state.show_last_two_messages else f"Calling model with message: {last_message.content}"
        state.show_last_two_messages = False
        consent_denied, state = self.is_consent_denied(state, mssg_to_display)
        if consent_denied:
            return state
        
        response = self.llm.invoke(messages)
        state.messages = state.messages + [response]
        return state
        
    def should_continue(self, state: AgentState) -> str:
        messages = state.messages
        last_message = messages[-1]
        print(f"Should Continue: {last_message.content}")

        if "EXECUTE" in last_message.content:
            return Node.EXECUTE.value
        
        return END

    def create_app(self) -> CompiledGraph:
        graph = StateGraph(AgentState)

        graph.add_node(Node.AGENT.value, self.call_model)
        graph.add_node(Node.EXECUTE.value, self.execute_code)

        graph.add_edge(START, Node.AGENT.value)
        graph.add_conditional_edges(Node.AGENT.value, self.should_continue, {
            Node.EXECUTE.value: Node.EXECUTE.value,
            END: END
        })
        graph.add_edge(Node.EXECUTE.value, Node.AGENT.value)

        return graph.compile()

    @with_langtrace_root_span()
    def create_and_invoke(self, state: AgentState) -> dict:
        app = self.create_app()
        final_state_response: dict = app.invoke(state)
        return final_state_response

    def run(self, data_dict: dict[str, pd.DataFrame], question: str, session_id: str)->str:
        print(session_id)
        self.globals_dict['data_dict'] = data_dict
        sample_data = {name: df.head().to_dict() for name, df in data_dict.items()}
        initial_message = SystemMessage(content=prompts.INITIAL.format(sample_data=sample_data))
        question_message = HumanMessage(content=prompts.QUESTION.format(question=question))

        final_state_response: dict = inject_additional_attributes(lambda: self.create_and_invoke(
            AgentState(messages=[initial_message, question_message], prev_results={}, human_stop=False, show_last_two_messages=False)
        ), {"user_id": session_id, "question": question})
        final_state = AgentState(**final_state_response)
        final_return = self.get_final_and_print_results(final_state)
        return final_return

    def get_final_and_print_results(self, final_state: AgentState) -> str:
        if self.debug_final_state:
            print("DEBUG: Final state structure:")
            print(final_state)

        if self.debug_conversation:
            for message in final_state.messages:
                if isinstance(message, SystemMessage):
                    print(f"System: {message.content}\n")
                elif isinstance(message, HumanMessage):
                    print(f"Human: {message.content}\n")
                elif isinstance(message, AIMessage):
                    print(f"AI: {message.content}\n")
                else:
                    print(f"Unknown message type: {type(message)}: {message.content}\n")

        last_message:AIMessage = final_state.messages[-1]
        if last_message.content.startswith("END"):
            content = last_message.content[3:].strip()
            print("Final Answer: ", content)
            return content

        if final_state.human_stop:
            print("User has stopped the conversation.")
            return "User stopped the conversation."