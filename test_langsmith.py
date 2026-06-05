from langchain_groq import ChatGroq
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()
llm = ChatGroq(model="qwen/qwen3-32b", temperature=0)
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


agent = create_agent(model=llm, tools=[get_weather])

output = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather in San Francisco?"}]}
)
print(output["messages"][-1].content)
