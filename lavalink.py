import os
import subprocess
import sys
import signal
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_lavalink():
    try:
        lavalink_dir = os.path.join(os.path.dirname(__file__), "lavalink")
        lavalink_jar = os.path.join(lavalink_dir, "Lavalink.jar")
        lavalink_config = os.path.join(lavalink_dir, "application.yml")

        logging.info(f"Lavalink directory: {lavalink_dir}")
        logging.info(f"Lavalink JAR file: {lavalink_jar}")
        logging.info(f"Lavalink config file: {lavalink_config}")

        if not os.path.exists(lavalink_jar):
            logging.error(f"Lavalink.jar not found at {lavalink_jar}")
            sys.exit(1)
            
        # Add Java memory settings for OpenJDK 21
        lavalink_proc = subprocess.Popen(
            [
                "java",
                "-Xmx256M",  # Максимальный размер кучи (256 MB)
                "-Xms128M",  # Начальный размер кучи (128 MB)
                "-XX:+UseG1GC",  # Использование сборщика мусора G1GC
                "-XX:MaxRAMPercentage=75.0",  # Ограничение использования памяти до 75% доступной
                "-jar",
                lavalink_jar,
                "--spring.config.location=file:" + lavalink_config,
            ],
            cwd=lavalink_dir,
        )

        logging.info("Lavalink server started")

        def signal_handler(signum, frame):
            logging.info("Shutting down Lavalink...")
            lavalink_proc.terminate()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        while True:
            returncode = lavalink_proc.poll()
            if returncode is not None:
                logging.error(f"Lavalink exited with code {returncode}")
                # Log stdout and stderr
                for line in lavalink_proc.stdout:
                    logging.info(line.strip())
                for line in lavalink_proc.stderr:
                    logging.error(line.strip())
                sys.exit(returncode)
            time.sleep(1)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_lavalink()