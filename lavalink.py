import asyncio
import os
import subprocess
import sys


def run_lavalink():
    lavalink_dir = os.path.join(os.path.dirname(__file__), "lavalink")
    print(lavalink_dir)
    lavalink_jar = os.path.join(lavalink_dir, "Lavalink.jar")
    print(lavalink_jar)
    lavalink_config = os.path.join(lavalink_dir, "application.yml")

    lavalink_proc = subprocess.Popen(
        [
            "java",
            "-jar",
            lavalink_jar,
            "--spring.config.location=file:" + lavalink_config,
        ],
        cwd=lavalink_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    run_lavalink()
