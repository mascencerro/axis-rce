#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import time

srv_run = True

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'GET request')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(b'POST request')
        response.write(b'Received: ')
        response.write(body)
        self.wfile.write(response.getvalue())

    def do_QUIT(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'QUIT called')
        global srv_run
        srv_run = False


httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)

while (srv_run == True):
    httpd.handle_request()




