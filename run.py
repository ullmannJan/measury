import measury
import logging
from pathlib import Path

script_dir = Path(__file__).parent.resolve()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.CRITICAL,
        format="%(asctime)s  %(levelname)-10s %(name)s: %(message)s",
    )
    logger = logging.getLogger("Measury")
    logger.setLevel(logging.INFO)
    # measury.run(logger=logger)
    # measury.run(file_path=script_dir/r"tests/test_data/test_file.msry", logger=logger)
    measury.run(file_path=script_dir / r"img/ZeissNIM_001.msry", logger=logger)
