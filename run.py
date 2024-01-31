import semmy
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL,
                        format='%(asctime)s  %(levelname)-10s %(name)s: %(message)s')
    logger = logging.getLogger("Semmy")
    logger.setLevel(logging.CRITICAL)
    semmy.run(logger=logger)
    # semmy.run(file_path=r"tests/test_data/test_file.semmy")
    # semmy.run(file_path=r"tests/test_data/test_image.tif")
    
    