from dotenv import load_dotenv

from stanley import Agent
from stanley.tools import AgentEndTaskTool, GoogleSearchTool

load_dotenv()


def main():
    agent = Agent(
        model="openai/gpt-4.1-mini", tools=[GoogleSearchTool(), AgentEndTaskTool()]
    )
    responses = agent.run(
        "Hi, can you please tell me how the weather is like in Sydney today?",
        stream=True,
    )
    for response in responses:
        print(response)


if __name__ == "__main__":
    main()
