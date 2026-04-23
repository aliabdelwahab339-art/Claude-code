"""Entry point: `python -m egyptian_voice_agent`."""

from __future__ import annotations

import uvicorn

from egyptian_voice_agent.config import settings


def main() -> None:
    uvicorn.run(
        "egyptian_voice_agent.server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
