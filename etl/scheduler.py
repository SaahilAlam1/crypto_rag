import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from etl.pipeline import run_etl

logger = logging.getLogger(__name__)


def job() -> None:
    result = run_etl(max_pages_per_category=3)
    logger.info("ETL run: %s", result)
    if result["inserted"]:
        try:
            from rag.index import build_index
            logger.info("Index rebuilt: %s", build_index(force=True))
        except Exception:
            logger.exception("Index rebuild failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", hours=1, next_run_time=datetime.now(), max_instances=1, coalesce=True)
    scheduler.start()
