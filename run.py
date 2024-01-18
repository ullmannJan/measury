import semmy
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL)
    # semmy.run()
    semmy.run(file_path=r"tests/test_data/test_file.semmy")
    # semmy.run(file_path=r"tests/test_data/test_image.tif")