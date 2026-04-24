from socket import *
import os

# Merges html file with css file into one file.
def inline_css(html_content, css_content):
    head_end_index = html_content.find("</head>")
    if head_end_index != -1:
        return html_content[:head_end_index] + f"<style>\n{css_content}\n</style>" + html_content[head_end_index:]
    return html_content


# Send the appropriate http response into the client socket depending on the header and the status code.
def send_response(client_socket, status_code, content_type, content=None):
    status_messages = {
        200: "200 OK",
        404: "404 Not Found",
        307: "307 Temporary Redirect"
    }
    client_socket.send(f"HTTP/1.1 {status_messages[status_code]}\r\n".encode())
    client_socket.send(f"Content-Type: {content_type}; charset=utf-8\r\n".encode())
    client_socket.send("\r\n".encode())
    if content:
        client_socket.send(content.encode())


# Determines the content type based on the file extension.
def get_content_type(filename):
    if filename.endswith(".html"):
        return "text/html"
    elif filename.endswith(".css"):
        return "text/css"
    elif filename.endswith(".jpg"):
        return "image/jpg"
    elif filename.endswith(".jpeg"):
        return "image/jpeg"
    elif filename.endswith(".png"):
        return "image/png"
    elif filename.endswith(".mp4"):
        return "video/mp4"
    else:
        return "application/octet-stream"


def handle_file_request(filename, filetype, client_socket):
    """Handle file requests with redirects if file not found"""
    filepath = os.path.join(".", "images" if filetype == "image" else "Videos", filename)

    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            content = f.read()
        send_response(client_socket, 200, get_content_type(filename))
        client_socket.send(content)
    else:
        # Redirect to Google search
        search_type = "tbm=isch" if filetype == "image" else "tbm=vid"
        redirect_url = f"https://www.google.com/search?{search_type}&q={filename.split('.')[0]}"
        send_response(client_socket, 307, "text/html",
                      f"<html><head><meta http-equiv='refresh' content='0; url={redirect_url}'></head></html>")


# Merges all html and css files to prepare them for http responses.
with open("main_en.html", "r", encoding='utf-8') as f:
    main_page_english_html = f.read()
with open("styles.css", "r", encoding='utf-8') as f:
    main_page_css = f.read()
main_english_page = inline_css(main_page_english_html, main_page_css)

with open("main_ar.html", "r", encoding='utf-8') as f:
    main_page_arabic_html = f.read()
main_arabic_page = inline_css(main_page_arabic_html, main_page_css)

with open("mySite_1221574_en.html", "r", encoding='utf-8') as f:
    supporting_page_english_html = f.read()
with open("request_styles.css", "r", encoding='utf-8') as f:
    supporting_page_css = f.read()
supporting_english_page = inline_css(supporting_page_english_html, supporting_page_css)

with open("mySite_1221574_ar.html", "r", encoding='utf-8') as f:
    supporting_page_arabic_html = f.read()
supporting_arabic_page = inline_css(supporting_page_arabic_html, supporting_page_css)




# Set up server
serverPort = 9954                       # Port derived from student ID 1221574 (last 4 digits: 1574 → 9954)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('0.0.0.0', serverPort))  # Server is accessible from any devices on the same network.
serverSocket.listen(5)  # Server can handle up to 5 clients at the same time.
print(f"Server is waiting for connection on port {serverPort}...")

while True:
    client_conn_socket, addr = serverSocket.accept()
    client_ip, client_port = addr
    error_page = f"""HTTP/1.1 404 Not Found\r

    <!DOCTYPE html>
    <html>
    <head>
        <title>Error 404</title>
    </head>
    <body>
        <h1>Error 404</h1>
        <p style="color: red; font-weight: bold; font-size: 24px;">The file is not found</p>
        <p>Client IP: {client_ip}<br>Client Port: {client_port}</p>
    </body>
    </html>
    """
    print(f"\nConnection from: {addr}")

    try:
        client_request = client_conn_socket.recv(1024).decode()
        print(f"Request received:\n{client_request}")

        if not client_request:
            continue

        # Parse the request
        request_lines = client_request.split('\n')
        if len(request_lines) == 0:
            continue

        request_line = request_lines[0]
        if ' ' not in request_line:
            continue

        method, path, _ = request_line.split(' ', 2)
        path = path.split('?')[0]  # Remove query parameters

        # Handle different paths
        if path in ['/', '/en', '/index.html', '/main_en.html']:
            send_response(client_conn_socket, 200, "text/html", main_english_page)
        elif path in ['/ar', '/main_ar.html']:
            send_response(client_conn_socket, 200, "text/html", main_arabic_page)
        elif path == '/mySite_1221574_en.html':
            send_response(client_conn_socket, 200, "text/html", supporting_english_page)
        elif path == '/mySite_1221574_ar.html':
            send_response(client_conn_socket, 200, "text/html", supporting_arabic_page)
        elif path == '/styles.css':
            send_response(client_conn_socket, 200, "text/css", main_page_css)
        elif path == '/request_styles.css':
            send_response(client_conn_socket, 200, "text/css", supporting_page_css)
        elif path.startswith('/images/') or path.startswith('/Videos/'):
            # Handle direct file requests
            filename = os.path.basename(path)
            filetype = 'image' if path.startswith('/images/') else 'video'
            handle_file_request(filename, filetype, client_conn_socket)
        elif path == '/request-file':
            # Handle form submissions from mySite page
            params = {}
            if '?' in request_line.split(' ')[1]:
                query = request_line.split(' ')[1].split('?')[1]
                params = dict(p.split('=') for p in query.split('&'))

            if 'filename' in params and 'fileType' in params:
                filename = params['filename']
                filetype = params['fileType']
                handle_file_request(filename, filetype, client_conn_socket)
            else:
                send_response(client_conn_socket, 404, "text/html", error_page)
        else:
            # Handle all other requests (404)
            send_response(client_conn_socket, 404, "text/html", error_page)

    except Exception as e:
        print(f"Error handling request: {e}")
        send_response(client_conn_socket, 404, "text/html", error_page)
    finally:
        client_conn_socket.close()