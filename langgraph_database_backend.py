from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
import sqlite3



load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

llm = ChatOpenAI(
    api_key=OPENROUTER_API_KEY,
    model='arcee-ai/trinity-large-preview:free',
    base_url="https://openrouter.ai/api/v1"
)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {'messages': [response]}


conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)


checkpoint = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpoint)


def retriev_all_threads() :
    all_threads = set()
    for checkpointer in checkpoint.list(None):
        all_threads.add(checkpointer.config['configurable']['thread_id'])
    return list(all_threads)