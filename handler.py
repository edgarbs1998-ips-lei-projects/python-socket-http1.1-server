import base64
import hashlib
import json
import mimetypes
import os
import select
import socket
import sys
import time
import uuid

import settings
from datetime import datetime

from cache import Cache


def thread(connection, address, logger):
    """Handle received data from client using a thread"""

    # Init cahce system
    cache = Cache(settings.SERVER_CACHE_SIZE)

    try:
        # Connection received
        logger.trace().info("Connection from address %s ..." % str(address))

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

            logger.trace().info("Received from address %s: %s" % (str(address), request))

            # Parse client request
            method, url, headers, body, keep_alive = __parse_header(request)
            logger.requests().info("Request received (address=%s; method=%s; url=%s)" % (str(address), method, url))

            # Handle client request
            content, content_type, content_encoding, content_lastmodified, status, keep_alive = __request(
                logger, cache, method, url, headers, body, keep_alive)

            # Prepare HTTP response
            response = __response(status, content, content_type, content_encoding, content_lastmodified)

            # Return HTTP response
            connection.sendall(response)

            if keep_alive is False:
                break

        # Close client connection
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

        logger.trace().info("Communication from address %s has been terminated..." % str(address))

    except socket.error as error:
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

        logger.trace().error("An error has occurred while processing connection from %s: %s" % (str(address), error))


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


def __request(logger, cache, method, url, headers, body, keep_alive):
    """Returns file content for client request"""

    if method == "HEAD" or method == "GET":
        if url.startswith("/private/"):
            base64_auth = base64.b64encode(
                (settings.PRIVATE_USERNAME + ":" + settings.PRIVATE_PASSWORD).encode("utf-8"))

            if "Authorization" not in headers:
                return None, None, None, None, 401, keep_alive

            auth_method, auth_credentials = headers["Authorization"].split()
            auth_credentials = auth_credentials.encode("utf-8")
            if auth_credentials != base64_auth:
                return None, None, None, None, 401, keep_alive

        if url == "/":
            url = "/index.html"
        file_path = settings.HTDOCS_PATH + url

        # Check if requested file is on the cache
        file_content, file_lastmodified = cache.get(file_path)

        # Check if browser cache is valid
        if __is_browser_cache_valid(file_lastmodified, method, headers):
            return None, None, None, None, 304, keep_alive

        file_type, file_encoding = mimetypes.guess_type(file_path, True)

        if file_content is None:
            try:
                # Simulate disk loading time of 100ms for cache system
                time.sleep(settings.SIMULATE_DISK_DELAY)

                # Get last modification time of the file
                file_lastmodified = os.path.getmtime(file_path)

                # Check if browser cache is valid
                if __is_browser_cache_valid(file_lastmodified, method, headers):
                    return None, None, None, None, 304, keep_alive

                # Return file content
                with open(file_path, "rb") as file:
                    file_content = file.read()

                # Update the cache with the newly opened file
                cache.update(file_path, file_content, file_lastmodified)
            except (FileNotFoundError, OSError):
                return None, None, None, None, 404, keep_alive  # Not Found

        return file_content, file_type, file_encoding, file_lastmodified,\
               "HEAD" if method == "HEAD" else 200, keep_alive  # HEAD / OK
    elif method == "POST":
        if headers["Content-Type"] != "application/x-www-form-urlencoded":
            return None, None, None, None, 415, keep_alive  # Unsupported Media Type

        # Get parameters from request
        response = {}

        if len(body) > 0:
            parameters = body.split("&")
            for parameter in parameters:
                key, value = parameter.split("=")
                response[key] = value

        while True:
            # Generate a random unique identifier
            post_uid = str(uuid.uuid4())
            post_file_path = "%s/%s.json" % (settings.UPLOADED_PATH, post_uid)

            # Check if the generate identifier already exists and if so regenerate it
            if not os.path.exists(post_file_path):
                break

        # Create the file and open it
        with open(post_file_path, "w") as post_file:
            logger.trace().info("Created %s file" % post_file_path)

            # Write post data to the file
            json.dump(response, post_file, indent=4)

        response["uid"] = post_uid
        return json.dumps(response).encode(settings.ENCODING),\
               "application/json", "utf-8", None, 201, keep_alive  # Created
    elif method == "DELETE":
        delete_path = "%s/%s.json" % (settings.UPLOADED_PATH, url)

        # Check if specified file exists
        if os.path.exists(delete_path):
            # Delete file
            os.remove(delete_path)
            logger.trace().info("Deleted %s file" % delete_path)

            # Return response to client
            return None, None, None, None, 204, keep_alive
        else:
            # Return response to client
            return None, None, None, None, 404, keep_alive
    elif method == "PUT":
        if headers["Content-Type"] != "application/x-www-form-urlencoded":
            return None, None, None, None, 415, keep_alive  # Unsupported Media Type

        put_path = "%s/%s.json" % (settings.UPLOADED_PATH, url)

        # Check if specified file exists
        if not os.path.exists(put_path):
            # Return response to client
            return None, None, None, None, 404, keep_alive

        # Get parameters from request
        put_data = {}

        if len(body) > 0:
            parameters = body.split("&")
            for parameter in parameters:
                key, value = parameter.split("=")
                put_data[key] = value

        # Open the file
        with open(put_path, "w") as put_file:
            # Write post data to the file
            json.dump(put_data, put_file, indent=4)
            logger.trace().info("Updated %s file" % put_path)

        # Return response to client
        return None, None, None, None, 204, keep_alive
    elif method == "PATCH":
        if headers["Content-Type"] != "application/x-www-form-urlencoded":
            return None, None, None, None, 415, keep_alive  # Unsupported Media Type

        patch_path = "%s/%s.json" % (settings.UPLOADED_PATH, url)

        # Check if specified file exists
        if not os.path.exists(patch_path):
            # Return response to client
            return None, None, None, None, 404, keep_alive

        try:
            # Read file json data
            with open(patch_path, "r+") as patch_file:
                patch_file_data = json.load(patch_file)

                # Update/create json file with passed parameters
                if len(body) > 0:
                    parameters = body.split("&")
                    for parameter in parameters:
                        key, value = parameter.split("=")
                        patch_file_data[key] = value

                # Delete file content
                patch_file.seek(0)
                patch_file.truncate()

                # Write updated data to the file
                patch_file.write(json.dumps(patch_file_data, indent=4))
                logger.trace().info("Updated %s file" % patch_file)
        except json.JSONDecodeError as error:
            logger.trace().error("An error has occurred while processing PATCH request due to malformed JSON: %s" %
                                 error)

            # Return response to client
            return None, None, None, None, None, keep_alive

        # Return response to client
        return None, None, None, None, 204, keep_alive
    else:
        return None, None, None, None, 501, keep_alive  # Not Implemented


def __response(status_code, content, content_type, content_encoding, content_lastmodified):
    """Returns HTTP response"""

    headers = []

    # Build HTTP response
    if status_code == 200:
        status = "200 OK"
        if settings.CLIENT_CACHE_ENABLE:
            headers.append("Cache-Control: public, max-age=%d" % settings.CLIENT_CACHE_AGE)
    elif status_code == 201:
        status = "201 Created"
    elif status_code == 204:
        status = "204 No Content"
    elif status_code == 304:
        status = "304 Not Modified"
    elif status_code == 401:
        status = "401 Unauthorized Status"
        headers.append("WWW-Authenticate: Basic realm='Access Private Zone', charset='UTF-8'")
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
    headers.append("Content-MD5: %s" % hashlib.md5(content))
    headers.append("Server: python-socket-http/%s python/%s" % (settings.VERSION, sys.version))

    if content_encoding is not None:
        headers.append("Content-Encoding: %s" % content_encoding)

    if content_lastmodified is not None:
        if content_lastmodified > datetime.now().timestamp():
            headers.append("Last-Modified: %s" % datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        else:
            headers.append("Last-Modified: %s" %
                           datetime.fromtimestamp(content_lastmodified).strftime("%a, %d %b %Y %H:%M:%S GMT"))

    header = "\n".join(headers)
    response = (header + "\n\n").encode(settings.ENCODING)
    response += content

    # Return encoded response
    return response


def __is_browser_cache_valid(lastmodified, method, headers):
    """Check if browser cache has the most recent file version """

    if settings.CLIENT_CACHE_ENABLE and method == "GET" and lastmodified is not None and "If-Modified-Since" in headers:
        cache_lastmodified = datetime.strptime(headers["If-Modified-Since"],
                                               "%a, %d %b %Y %H:%M:%S GMT").timestamp()
        if cache_lastmodified <= datetime.now().timestamp() and int(cache_lastmodified) == int(lastmodified):
            return True
    return False
