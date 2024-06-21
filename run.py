import semmy
import logging
from pathlib import Path
script_dir = Path(__file__).parent.resolve()

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL,
                        format='%(asctime)s  %(levelname)-10s %(name)s: %(message)s')
    logger = logging.getLogger("Semmy")
    logger.setLevel(logging.INFO)
    # semmy.run(logger=logger)
    # semmy.run(file_path=script_dir/r"tests/test_data/test_file.semmy", logger=logger)
    semmy.run(file_path=script_dir/r"img/GUZ_001.tif", logger=logger)
    