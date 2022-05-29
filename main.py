import argparse
import logging
import re
import subprocess
import sys
import time
import yaml

TEMPLATE = {
    "keenetic": {
        "extension": ".keenetic",
        "template" : "ip route {ip:20} {gateway}"
    },
    "windows" : {
        "extension": ".bat",
        "template" : "route ADD {ip:20} MASK 255.255.255.255 {gateway}"
    },
    "linux"   : {
        "extension": ".sh",
        "template" : "route add -host {ip:20} gw {gateway}"
    }
}

def args():
    parser   = argparse.ArgumentParser(description="Generate and/or update routes.")
    parser.add_argument("-c", "--conf", metavar="\b", default="config.yml", help="Path to configuration file with a gateway and domains (default: config.yml)")
    parser.add_argument("-d", "--delay", metavar="\b", default=0, help="Delay before execution")
    parser.add_argument("-o", "--os", metavar="\b", default="keenetic", help="One of the operating systems: keenetic, windows, linux (default: keenetic)")
    parser.add_argument("-u", "--update", action="store_true", help="Use this flag to update routes on a router")
    parser.add_argument("-r", "--router", metavar="\b", default="admin@192.168.1.1", help="Hostname or ip address to update routes on (default: admin@192.168.1.1)")
    parser.add_argument("-p", "--password", metavar="\b", help="Password in case it required on the host")
    parser.add_argument("-l", "--log", metavar="\b", help="Log file to write log in.")
    args = parser.parse_args()
    args.delay = int(args.delay)
    return args

def routes(os, gateway, domains, update, router, password, log):

    # logging initial setup
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]  %(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if log:
        fileHandler = logging.FileHandler(f"{log}")
        fileHandler.setFormatter(logFormatter)
        logger.addHandler(fileHandler)
    else:
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(logFormatter)
        logger.addHandler(consoleHandler)

    ip_regex = re.compile("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    os = TEMPLATE[os]
    routes = []
    logger.info(f"Digging all the domains from the list. ({len(domains)} domains in total)")
    try:
        for domain in domains:
            ips = list(filter(ip_regex.match, [str(item)[2:-1] for item in subprocess.check_output(["dig", "+short", domain]).split()]))
            for ip in ips:
                route = eval(f'f"{os["template"]}"')
                routes.append(route)
        logger.info("Digging complete.")
        routes = list(set(routes))
        open("routes" + os["extension"], "w+").write("\n".join(routes))
    except subprocess.CalledProcessError:
        logger.info("Digging failed. Reading routes from the file ({'routes' + os['extension']}).")
        routes = open("routes" + os["extension"]).read().split("\n")
    if update:
        logger.info("Updating routes on the device:")
        for route in routes:
            logger.info(f"Updating {routes.index(route)+1}/{len(routes)} ({route.split()[2]}).")
            if password:
                command = f"sshpass -p {password} ssh {router} {route}"
            else:
                command = f"ssh {router} {route}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            with process.stdout:
                try:
                    for line in iter(process.stdout.readline, b""):
                        log_line = line.replace(b"\x1b[K", b"").decode("utf-8").strip()
                        if len(log_line) > 0:
                            logger.info(log_line)
                except subprocess.CalledProcessError as e:
                    logger.error(f"{str(e)}")
        logger.info("Updating complete.")

if __name__ == '__main__':
    args = args()
    config   = yaml.load(open(args.conf).read(), Loader=yaml.Loader)
    gateway  = config["gateway"]
    domains  = config["domains"]
    time.sleep(args.delay)
    routes(os=args.os, gateway=gateway, domains=domains, update=args.update, router=args.router, password=args.password, log=args.log)
