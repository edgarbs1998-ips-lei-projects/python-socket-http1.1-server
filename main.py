import socket
from datetime import datetime

import settings

# Create socket
from handler import Handler

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((settings.SERVER_HOST, settings.SERVER_PORT))
server_socket.listen()
print("[%s] Server listening on host %s and port %s ..."
      % (datetime.now().strftime(settings.DATETIME_FORMAT), settings.SERVER_HOST, settings.SERVER_PORT))

while True:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    # Set connection socket timeout
    client_connection.settimeout(settings.SOCKET_TIMEOUT)

    # Start a new thread for the client
    Handler(client_connection, client_address).start()

# Close socket
server_socket.close()
