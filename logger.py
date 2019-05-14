import logging


def init(trace_logger, trace_file, requests_logger, requests_file, level, formatter, date_format):
    # Trace log configuration startup
    trace_filehandler = logging.FileHandler(trace_file)
    trace_filehandler.setLevel(logging.getLevelName(level))
    trace_formatter = logging.Formatter(formatter)
    trace_filehandler.setFormatter(trace_formatter)
    logging.getLogger(trace_logger).addHandler(trace_filehandler)

    # Requests log configuration startup
    request_filehandler = logging.FileHandler(requests_file)
    request_filehandler.setLevel(logging.INFO)
    request_formatter = logging.Formatter(formatter)
    request_filehandler.setFormatter(request_formatter)
    logging.getLogger(requests_logger).addHandler(request_filehandler)

    # Console log configuration startup (log trace messages with level INFO or higher)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter(fmt=formatter, datefmt=date_format)
    console.setFormatter(console_formatter)
    logging.getLogger(trace_logger).addHandler(console)
