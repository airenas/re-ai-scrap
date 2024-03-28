import time

from ai_scrap.utils.logger import logger


class Timer:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info(f"finish {self.name} in {time.perf_counter() - self.start:.3f}s")
