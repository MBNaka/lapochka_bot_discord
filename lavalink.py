import os
import subprocess
import sys
import signal
import time
import logging
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LavalinkServer:
    def __init__(self):
        self.lavalink_dir = os.path.join(os.path.dirname(__file__), "lavalink")
        self.lavalink_jar = os.path.join(self.lavalink_dir, "Lavalink.jar")
        self.lavalink_config = os.path.join(self.lavalink_dir, "application.yml")
        self.process = None

    def start(self):
        if not os.path.exists(self.lavalink_jar):
            logging.error(f"Lavalink.jar not found at {self.lavalink_jar}")
            sys.exit(1)

        logging.info(f"Lavalink directory: {self.lavalink_dir}")
        logging.info(f"Lavalink JAR file: {self.lavalink_jar}")
        logging.info(f"Lavalink config file: {self.lavalink_config}")

        self.process = subprocess.Popen(
            [
                "java",
                "-Xmx256M",
                "-Xms128M",
                "-XX:+UseG1GC",
                "-XX:MaxRAMPercentage=75.0",
                "-jar",
                self.lavalink_jar,
                "--spring.config.location=file:" + self.lavalink_config,
            ],
            cwd=self.lavalink_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Объединяем stderr в stdout
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )

        # Поток для вывода логов в реальном времени
        log_thread = threading.Thread(target=self._stream_logs, daemon=True)
        log_thread.start()

        logging.info("Lavalink server started")

        def signal_handler(signum, frame):
            logging.info("Shutting down Lavalink...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Основной цикл — просто ждём, пока процесс жив
        while self.process.poll() is None:
            time.sleep(1)

        logging.error(f"Lavalink exited with code {self.process.returncode}")
        sys.exit(self.process.returncode)

    def _stream_logs(self):
        """Читаем вывод процесса и логируем в реальном времени"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                line = line.rstrip()
                if line:
                    logging.info(f"[Lavalink] {line}")
        except Exception as e:
            logging.error(f"Error reading Lavalink output: {e}")

if __name__ == "__main__":
    server = LavalinkServer()
    server.start()
