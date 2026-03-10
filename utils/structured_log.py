from typing import Any


def _render(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ")


def with_context(message: str, **context: Any) -> str:
    if not context:
        return message
    pairs = " ".join(f"{key}={_render(value)}" for key, value in sorted(context.items()))
    return f"{message} | {pairs}"


def log_event(logger, level: str, message: str, **context: Any) -> None:
    log_fn = getattr(logger, level, logger.info)
    log_fn(with_context(message, **context))
