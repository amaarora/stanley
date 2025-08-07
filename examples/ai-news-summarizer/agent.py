from dotenv import load_dotenv
from tools.readblogpost import ReadBlogPostTool
from tools.searchlinkedin import SearchLinkedInTool

from stanley import Agent
from stanley.tools import AgentEndTaskTool

load_dotenv()


def main():
    with open("system_prompt.txt") as f:
        system_prompt = f.read()

    agent = Agent(
        model="anthropic/claude-3-5-sonnet-20241022",
        tools=[SearchLinkedInTool(), ReadBlogPostTool(), AgentEndTaskTool()],
        system_prompt=system_prompt,
    )

    response = agent.run("Hello! Please help me analyze some content.", stream=True)
    for chunk in response:
        print(chunk)


if __name__ == "__main__":
    main()
