# log_util.py
# Minimal logger for the Vossberg Mobility nightly run.

import time

LOG_LINES: list[str] = []  # global buffer, flushed to disk by flush_log()


def log(message: str) -> None:
    """Append a timestamped entry to the buffer and print it."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    LOG_LINES.append(line)
    print(line)


def flush_log(path: str) -> None:
    """Write buffered log lines to path (append) then clear the buffer."""
    with open(path, "a") as f:
        for line in LOG_LINES:
            f.write(line + "\n")
    LOG_LINES.clear()
