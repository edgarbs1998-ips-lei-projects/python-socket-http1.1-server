import base64
import os
import json
import mimetypes
import select
import socket
import settings
from datetime import datetime


def thread(connection, address, log):
    """Handle received data from client"""

    try:
        # Connection received
        log.trace().info("Connection from address %s ..." % str(address))

        while True:
            readable, writable, exceptional = select.select([connection], [], [connection], settings.KEEP_ALIVE_SECONDS)
            if exceptional or not readable:
                break

            try:
                request = connection.recv(settings.BUFSIZE).decode(settings.ENCODING)

                if not request:
                    break
            except OSError:
                break

            log.trace().info("Received from address %s: %s" % (str(address), request))

            # Parse client request
            method, url, headers, body, keep_alive = __parse_header(request)
            log.requests().info("Request received (address=%s; method=%s; url=%s)" %
                                (str(address), method, url))

            # Handle client request
            content, content_type, content_encoding, status, keep_live = __request(
                method, url, headers, body, keep_alive, log)

            # Prepare HTTP response
            response = __response(status, content, content_type, content_encoding)

            # Return HTTP response
            connection.sendall(response)

            if keep_live is False:
                break

        # Close client connection
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

        log.trace().info("Communication from address %s has been terminated..." % str(address))

    except socket.error as error:
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

        log.trace().error("An error has occurred while processing connection from %s: %s" % (str(address), error))


def __parse_header(request):
    """Returns parsed headers"""

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
    url = request_header[1]

    return method, url, headers, body, keep_alive


def __request(method, url, headers, body, keep_alive, log):
    """Returns file content for client request"""

    if method == "HEAD" or method == "GET":
        if url.startswith("/private/"):
            base64_auth = base64.b64encode(
                (settings.PRIVATE_USERNAME + ":" + settings.PRIVATE_PASSWORD).encode("utf-8"))

            if "Authorization" not in headers:
                return None, None, None, 401, keep_alive

            auth_method, auth_credentials = headers["Authorization"].split()
            auth_credentials = auth_credentials.encode("utf-8")
            if auth_credentials != base64_auth:
                return None, None, None, 401, keep_alive

        if url == "/":
            url = "/index.html"

        file_type, file_encoding = mimetypes.guess_type(settings.HTDOCS_PATH + url, True)

        try:
            # Return file content
            with open(settings.HTDOCS_PATH + url, "rb") as file:
                return file.read(), file_type, file_encoding, "HEAD" if method == "HEAD" else 200, keep_alive  # HEAD / OK
        except FileNotFoundError:
            return None, None, None, 404, keep_alive  # Not Found

    elif method == "POST":
        if headers["Content-Type"] != "application/x-www-form-urlencoded":
            return None, None, None, 415, keep_alive  # Unsupported Media Type

        # Get parameters from request
        response = {}

        if len(body) > 0:
            parameters = body.split("&")
            for parameter in parameters:
                key, value = parameter.split("=")
                response[key] = value

        # Create file id
        response["id"] = datetime.now().strftime("%Y%m%d%H%M")

        # Check if file exists to avoid erros in server side
        if not os.path.exists("%s/%s.json" % (settings.UPLOADED_USER_PATH, response["id"])):
            # Create user json file
            _create_file = open("%s/%s.json" % (settings.UPLOADED_USER_PATH, response["id"]), "x")

            # Send log to server log file
            log.trace().info("Created file in path %s/%s.json"
                             % (settings.UPLOADED_USER_PATH, response["id"]))

            # Open user json file and write user data
            _file = open("%s/%s.json" % (settings.UPLOADED_USER_PATH, response["id"]), "w+")

            # Delete id from response data
            response.pop("id", None)

            # Write data to file
            _file.write(json.dumps(response))

        else:
            # Open user json file and write user data
            _file = open("%s/%s.json" % (settings.UPLOADED_USER_PATH, response["id"]), "w+")

            # Send log to server log file
            log.trace().info("Rewrited file in path %s/%s.json"
                             % (settings.UPLOADED_USER_PATH, response["id"]))

            # Delete id from response data
            response.pop("id", None)

            # Write data to file
            _file.write(json.dumps(response))

        return json.dumps(response).encode(settings.ENCODING), "application/json", "utf-8", 201, keep_alive  # Created

    elif method == "DELETE":
        if headers["Content-Type"] != "application/x-www-form-urlencoded":
            return None, None, None, 415, keep_alive  # Unsupported Media Type

        # Get parameters from request
        response = {}

        if len(body) > 0:
            parameters = body.split("&")
            for parameter in parameters:
                key, value = parameter.split("=")
                response[key] = value

        # Check if generated-id exists
        if response["generated-id"]:
            if os.path.exists("%s/%s.json" % (settings.UPLOADED_USER_PATH, response["generated-id"])):

                # Delete file
                os.remove("%s/%s.json" % (settings.UPLOADED_USER_PATH, response["generated-id"]))

                # Send log to server log file
                log.trace().info("Deleted file in path %s/%s.json"
                                 % (settings.UPLOADED_USER_PATH, response["generated-id"]))

        # Return response to client
        return json.dumps(response).encode(settings.ENCODING), "application/json", "utf-8", 200, keep_alive
    else:
        return None, None, None, 501, keep_alive  # Not Implemented


def __response(status_code, content, content_type, content_encoding):
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

    if content_encoding is not None:
        headers.append("Content-Encoding: %s" % content_encoding)

    header = "\n".join(headers)
    response = (header + "\n\n").encode(settings.ENCODING)
    response += content

    # Return encoded response
    return response
