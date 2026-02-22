import asyncio
import logging
import time

log = logging.getLogger(__name__)


async def _run_one(
    label: str, model: dict, messages: list[dict],
) -> tuple[str, str | None, float]:
    start = time.time()
    try:
        result = await asyncio.to_thread(model["generate"], messages)
        return label, result, time.time() - start
    except Exception as e:
        log.error("   [%s] %s — error: %s", label, model["name"], e)
        return label, None, time.time() - start


def generate_parallel(
    tasks: list[tuple],
) -> list[tuple[str, str | None, float]]:
    async def _run_all() -> list[tuple[str, str | None, float]]:
        return await asyncio.gather(*(_run_one(*t) for t in tasks))

    return asyncio.run(_run_all())
