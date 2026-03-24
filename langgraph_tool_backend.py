from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from ddgs import DDGS
from langchain_core.tools import tool
import os, random, requests
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


def ddg_search(query: str) -> dict:
    """
    It can search the web and retrieve information
    """
    with DDGS() as ddgs:
        results = ddgs.text(query, region="us-en", max_results=5)
        return {'search_result': results}
    

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmatic operation on two numbers.
    Supported operations: add, sub, mult, div
    """

    try:
        if operation == 'add':
            result = first_num + second_num
        elif operation == 'sub':
            result = first_num - second_num
        elif operation == 'mult':
            result = first_num * second_num
        elif operation == 'div':
            if second_num == 0:
                return {'error': 'division by 0 is not allowed'}
            result = first_num / second_num
        else :
            return {'error': f'unsupported operation "{operation}"'}
        
        return {
            'first_num': first_num, 'second_num': second_num,
            'opeartion': operation, 'result': result
            }
    except Exception as e:
        return {'error': str(e)}


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for given symbol (e.g. 'AAPL', 'TSLA') for a company using Alpha Vantage with API key in the URL.
    """
    apikey = "5DDFOKTR4NTR0RYR"
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTES&symbol={symbol}&apikey={apikey}"
    r = requests.get(url)
    return r.json()

tools = [get_stock_price, calculator, ddg_search]

llm_with_tools = llm.bind_tools(tools)


def chat_node(state: ChatState):
    """
    LLM node that may answer or request a tool call.
    """
    messages = state['messages']
    response = llm_with_tools.invoke(messages)

    return {'messages': [response]}

tool_node = ToolNode(tools)



conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)


checkpoint = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpoint)


def retriev_all_threads() :
    all_threads = set()
    for checkpointer in checkpoint.list(None):
        all_threads.add(checkpointer.config['configurable']['thread_id'])
    return list(all_threads)