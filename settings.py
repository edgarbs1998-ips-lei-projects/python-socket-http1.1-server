# Server version
VERSION = "1.0.0"

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
HTDOCS_PATH = "./htdocs"
SOCKET_TIMEOUT = 30
KEEP_ALIVE_SECONDS = 10
UPLOADED_PATH = "%s/%s" % (HTDOCS_PATH, "uploaded")

# Cache settings
SIMULATE_DISK_DELAY = 0.1
SERVER_CACHE_SIZE = 2
CLIENT_CACHE_ENABLE = True
CLIENT_CACHE_AGE = 31536000  # Seconds

# Communication settings
BUFSIZE = 4096
ENCODING = "utf-8"

# Logger settings
LOG_TRACE_FILE = "./logs/trace.txt"
LOG_REQUESTS_FILE = "./logs/log.txt"
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "[%(asctime)s - %(name)s - %(levelname)s] - %(message)s"

# Private auth
PRIVATE_USERNAME = "admin"
PRIVATE_PASSWORD = "qwerty"