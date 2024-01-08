from semmy import app
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run()
    # app.run(file_path=r"img/2023-04-24_PTB_D5_10-01.semmy")

# TODO
#
# Saving
# - readable output
# - restrict to one type of measurement per structure
# - average over measurements
#
# Settings
# - proper output of settings file# - settings page
# - sem_db with more properties