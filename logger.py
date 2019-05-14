import logging


def init(file, level, format, date_format):
    # Log configuration startup
    logging.basicConfig(level=logging.getLevelName(level),
                        format=format,
                        datefmt=date_format,
                        filename=file,
                        filemode='w'
                        )

    # Define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    # Set a format which is simpler for console use
    formatter = logging.Formatter(format)

    # Tell the handler to use this format
    console.setFormatter(formatter)

    # Add the handler to the root logger
    logging.getLogger('').addHandler(console)
