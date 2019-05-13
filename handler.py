import base64
import imghdr
import json
import select
import sndhdr
import socket
import threading
from datetime import datetime

import settings


class Handler(threading.Thread):
    def __init__(self, connection, address, log):
        super().__init__()
        self.__connection = connection
        self.__address = address
        self.log = log

    def run(self):
        """Handle received data from client"""

        try:
            # Connection received
            self.log.info("Connection from address %s ..."
                          % str(self.__address))

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

                self.log.info("Received from address %s: %s"
                              % (self.__address, request))

                # Handle client request
                content, content_type, status, keep_live = self.__request(request)

                # Prepare HTTP response
                response = self.__response(status, content, content_type)

                # Return HTTP response
                self.__connection.sendall(response)

                if keep_live is False:
                    break

            # Close client connection
            self.__connection.shutdown(socket.SHUT_RDWR)
            self.__connection.close()

            self.log.info("Communication from address %s has been terminated..."
                          % str(self.__address))

        except socket.error as error:
            self.__connection.shutdown(socket.SHUT_RDWR)
            self.__connection.close()

            self.log.error("An error has occurred while processing connection from %s: %s"
                           % (self.__address, error))

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

        keep_alive = True
        if "Connection" in headers and headers["Connection"] == "close":
            keep_alive = False

        request_header = headers_body[0].split()
        method = request_header[0]
        filename = request_header[1]

        if method == "HEAD" or method == "GET":
            # TODO Improve auth code
            if filename.startswith("/private/"):
                user_pass = settings.PRIVATE_USERNAME + ":" + settings.PRIVATE_PASSWORD
                base64_auth = base64.b64encode(user_pass.encode("utf-8"))

                if "Authorization" in headers:
                    auth_method, auth_credentials = headers["Authorization"].split()
                    auth_credentials = auth_credentials.encode("utf-8")
                    if auth_credentials != base64_auth:
                        return None, None, 401, keep_alive
                else:
                    return None, None, 401, keep_alive

            if filename == "/":
                filename = "/index.html"

            # TODO Improve file type detection code
            image_type = imghdr.what(settings.HTDOCS_PATH + filename)
            if image_type is not None:
                content_type = "image/" + image_type
            else:
                # TODO Support better audio files
                sound_type = sndhdr.what(settings.HTDOCS_PATH + filename)
                if sound_type is not None:
                    content_type = "audio/" + sound_type[0]
                else:
                    content_type = "text/html"

            try:
                # Return file content
                with open(settings.HTDOCS_PATH + filename, "rb") as file:
                    return file.read(), content_type, "HEAD" if method == "HEAD" else 200, keep_alive  # HEAD / OK
            except FileNotFoundError:
                return None, None, 404, keep_alive  # Not Found
        elif method == "POST":
            if headers["Content-Type"] != "application/x-www-form-urlencoded":
                return None, None, 415, keep_alive  # Unsupported Media Type

            response = {}

            if len(body) > 0:
                parameters = body.split("&")
                for parameter in parameters:
                    key, value = parameter.split("=")
                    response[key] = value

            return json.dumps(response).encode(settings.ENCODING), "application/json", 201, keep_alive  # Created
        else:
            return None, None, 501, keep_alive  # Not Implemented

    def __response(self, status_code, content, content_type):
        """Returns HTTP response"""

        headers = []

        # Build HTTP response
        if status_code == 200:
            status = "200 OK"
        elif status_code == 201:
            status = "201 Created"
        elif status_code == 401:
            status = "401 Unauthorized Status"
            headers.append("WWW-Authenticate: Basic realm='Access Private Folder', charset='UTF-8'")
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

        if content is None:
            content = "".encode(settings.ENCODING)
        if content_type is None:
            content_type = "text/plain"

        headers.insert(0, "HTTP/1.1 %s" % status)
        headers.append("Date: %s" % datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        headers.append("Connection: keep-alive")
        headers.append("Content-Type: %s" % content_type)
        headers.append("Content-Length: %d" % len(content))

        header = "\n".join(headers)
        response = (header + "\n\n").encode(settings.ENCODING)
        response += content

        # Return encoded response
        return response
