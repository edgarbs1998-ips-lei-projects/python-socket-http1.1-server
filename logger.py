# Created by Luis Varela

import logging


class Logger:
    def __init__(self, log_file, log_format, log_fmt):

        # Class parameters

        self.log_file = log_file
        self.log_format = log_format
        self.log_fmt = log_fmt

        # Log configuration startup

        logging.basicConfig(level=logging.DEBUG,
                            format=self.log_format,
                            datefmt=self.log_fmt,
                            filename=self.log_file,
                            filemode='w'
                            )

        # Define a Handler which writes INFO messages or higher to the sys.stderr

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)

        # Set a format which is simpler for console use

        formatter = logging.Formatter(self.log_format)

        # Tell the handler to use this format

        console.setFormatter(formatter)

        # Add the handler to the root logger

        logging.getLogger('').addHandler(console)

    def info(self, message):
        logging.info(message)

    def warning(self, message):
        logging.warning(message)

    def error(self, message):
        logging.error(message)
