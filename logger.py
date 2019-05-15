import logging


class Logger:
    def __init__(self, trace_file, requests_file, level, formatter, date_format):

        # Class parameters
        self.logger_trace = logging.getLogger("trace")
        self.logger_requests = logging.getLogger("requests")

        # Console log configuration startup (log to console every INFO or higher level message, independent of logger)
        logging.basicConfig(level=logging.INFO,
                            format=formatter,
                            datefmt=date_format
                            )

        # Setup log messages formatter
        formatter = logging.Formatter(fmt=formatter, datefmt=date_format)

        # Trace log configuration startup
        trace_handler = logging.FileHandler(trace_file, mode="a")
        trace_handler.setLevel(logging.getLevelName(level))
        trace_handler.setFormatter(formatter)
        self.logger_trace.addHandler(trace_handler)

        # Trace log configuration startup
        requests_handler = logging.FileHandler(requests_file, mode="a")
        requests_handler.setLevel(logging.getLevelName(level))
        requests_handler.setFormatter(formatter)
        self.logger_requests.addHandler(requests_handler)

    def trace(self):
        return self.logger_trace

    def requests(self):
        return self.logger_requests
