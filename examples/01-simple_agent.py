from dotenv import load_dotenv

from stanley import Agent

load_dotenv()


def main():
    agent = Agent(model="openai/gpt-4.1-mini")
    responses = agent.run("Hi", stream=False)
    print(responses)


if __name__ == "__main__":
    main()
