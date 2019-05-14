import socket
import threading
import handler
import settings
import logger
import logging

logger.init(settings.LOG_FILE, settings.LOG_LEVEL, settings.LOG_FORMAT, settings.DATETIME_FORMAT)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((settings.SERVER_HOST, settings.SERVER_PORT))
server_socket.listen()

# print("[%s] Server listening on host %s and port %s ..."
#     % (datetime.now().strftime(settings.DATETIME_FORMAT), settings.SERVER_HOST, settings.SERVER_PORT))

logging.info("Server listening on host %s and port %s ..." % (settings.SERVER_HOST, settings.SERVER_PORT))

while True:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    # Set connection socket timeout
    client_connection.settimeout(settings.SOCKET_TIMEOUT)

    # Start a new thread for the client
    threading.Thread(target=handler.thread, args=(client_connection, client_address)).start()

# Close socket
server_socket.close()
