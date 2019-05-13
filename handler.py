import json
import select
import socket
import threading
from datetime import datetime

import settings


class Handler(threading.Thread):
    def __init__(self, connection, address):
        super().__init__()
        self.__connection = connection
        self.__address = address

    def run(self):
        """Handle received data from client"""

        try:
            print("[%s] Connection from address %s..."
                  % (datetime.now().strftime(settings.DATETIME_FORMAT), self.__address))

            while True:
                # TODO “Connection: close" from the client

                readable, writable, exceptional = select.select([self.__connection], [],
                                                                [self.__connection], settings.KEEP_ALIVE_SECONDS)
                if exceptional or not readable:
                    break

                try:
                    request = self.__connection.recv(settings.BUFSIZE).decode(settings.ENCODING)

                    if not request:
                        break
                except OSError:
                    break

                print("[%s] Received from address %s: %s"
                      % (datetime.now().strftime(settings.DATETIME_FORMAT), self.__address, request))

                # Handle client request
                content, content_type, status = self.__request(request)

                # Prepare HTTP response
                response = self.__response(status, content, content_type)

                # Return HTTP response
                self.__connection.sendall(response)

            # Close client connection
            self.__connection.shutdown(socket.SHUT_RDWR)
            self.__connection.close()
            print("[%s] Communication from address %s has been terminated..."
                  % (datetime.now().strftime(settings.DATETIME_FORMAT), self.__address))
        except socket.error as error:
            self.__connection.shutdown(socket.SHUT_RDWR)
            self.__connection.close()
            print("[%s] An error has occurred while processing connection from %s: %s"
                  % (datetime.now().strftime(settings.DATETIME_FORMAT), self.__address, error))

    def __request(self, request):
        """Returns file content for client request"""

        # TODO Create header parsing function
        # Parse headers
        headers_body = request.splitlines()
        body_index = headers_body.index("")
        headers = {}
        for header in headers_body[1:body_index]:
            key, value = header.split(": ")
            headers[key] = value
        try:
            body = headers_body[body_index + 1:][0]
        except IndexError:
            body = ""

        request_header = headers_body[0].split()
        method = request_header[0]
        url = request_header[1]

        if method == "HEAD" or method == "GET":
            filename = url
            if filename == "/":
                filename = "/index.html"

            content_type = "text/html"  # TODO Set the correct content type

            try:
                # Return file content
                with open(settings.HTDOCS_PATH + filename, "rb") as file:
                    return file.read(), content_type, "HEAD" if method == "HEAD" else 200  # HEAD / OK
            except FileNotFoundError:
                return None, None, 404  # Not Found
        elif method == "POST":
            if headers["Content-Type"] != "application/x-www-form-urlencoded":
                return None, None, 415  # Unsupported Media Type

            response = {}

            if len(body) > 0:
                parameters = body.split("&")
                for parameter in parameters:
                    key, value = parameter.split("=")
                    response[key] = value

            return json.dumps(response).encode(settings.ENCODING), "application/json", 201  # Created
        else:
            return None, None, 501  # Not Implemented

    def __response(self, status_code, content, content_type):
        """Returns HTTP response"""

        headers = []

        # Build HTTP response
        if status_code == 200:
            status = "200 OK"
        elif status_code == 201:
            status = "201 Created"
        elif status_code == 404:
            status = "404 Not Found"
            content = "Requested resource not found".encode(settings.ENCODING)
        elif status_code == 415:
            status = "415 Unsupported Media Type"
            content = "Post content-type is not supported by the server".encode(settings.ENCODING)
        elif status_code == 501:
            status = "501 Not Implemented"
            content = "Request method is not supported by the server".encode(settings.ENCODING)
        elif status_code == "HEAD":
            status = "200 OK"
        else:
            status = "500 Internal Server Error"
            content = "An internal server error occurred while processing your request".encode(settings.ENCODING)

        if content_type is None:
            content_type = "text/plain"

        headers.append("HTTP/1.1 %s" % status)
        headers.append("Date: %s" % datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        headers.append("Connection: keep-alive")
        headers.append("Content-Type: %s" % content_type)
        headers.append("Content-Length: %d" % len(content))

        header = "\n".join(headers)
        response = (header + "\n\n").encode(settings.ENCODING)
        response += content

        # Return encoded response
        return response
