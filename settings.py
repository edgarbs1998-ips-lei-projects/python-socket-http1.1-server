# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
HTDOCS_PATH = "./htdocs"
SOCKET_TIMEOUT = 30
KEEP_ALIVE_SECONDS = 10

# Communication settings
BUFSIZE = 4096
ENCODING = "utf-8"

# Log settings
LOG_TRACE_FILE = "./logs/trace.txt"
LOG_REQUESTS_FILE = "./logs/log.txt"
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "[%(asctime)s - %(name)s - %(levelname)s] - %(message)s"

# Private auth
PRIVATE_USERNAME = "admin"
PRIVATE_PASSWORD = "qwerty"