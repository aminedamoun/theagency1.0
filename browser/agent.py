import logging

from browser_use import Agent
from browser_use.llm.models import ChatOpenAI

from config import load_config

logger = logging.getLogger("amine-agent")


async def run_browser_task(task: str) -> str:
    """Run a browser task and return the result summary."""
    cfg = load_config()
    llm_cfg = cfg["llm"]

    logger.info(f"[browser] Starting task: {task}")

    llm = ChatOpenAI(model=llm_cfg["model"])

    agent = Agent(
        task=task,
        llm=llm,
        max_actions_per_step=5,
    )

    result = await agent.run()

    final = result.final_result() if result.final_result() else "No result returned."
    logger.info(f"[browser] Task complete. Result: {final}")
    return final
