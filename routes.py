import argparse
import yaml
import subprocess
import re
from yaml.loader import Loader

def args():
    parser   = argparse.ArgumentParser(description="Generate and/or update routes.")
    parser.add_argument("-c", "--conf", metavar="\b", default="routes.yml", help="Path to configuration file with a gateway and domains (default: routes.yml)")
    parser.add_argument("-o", "--os", metavar="\b", default="keenetic", help="One of the operating systems: keenetic, windows (default: keenetic)")
    parser.add_argument("-u", "--update", action="store_true", help="Use this flag to update routes on a router")
    parser.add_argument("-r", "--router", metavar="\b", default="router", help="Hostname or ip address to update routes on (default: router)")
    parser.add_argument("-p", "--password", metavar="\b", help="Password in case it required on the host")
    return parser.parse_args()

def create_routes(os, domains, gateway):
    ip_regex = re.compile("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    routes = []
    for domain in domains:
        ips = list(filter(ip_regex.match, [str(item)[2:-1] for item in subprocess.check_output(["dig", "+short", domain]).split()]))
        for ip in ips:
            route = eval(f'f"{os["template"]}"')
            routes.append(route)
    open("routes" + os["extension"], "w+").write("\n".join(routes))

def update_routes(os, router, password):
    routes = open("routes" + os["extension"]).read().split('\n')
    for route in routes:
        cmd = f"sshpass -p {password} ssh {router} {route}".split()
        print(subprocess.check_output(cmd))

if __name__ == '__main__':
    os = {
        "keenetic": {
            "extension": ".keenetic",
            "template": "ip route {ip:15} {gateway} OpenVPN0"
        },
        "windows": {
            "extension": ".bat",
            "template": "route ADD {ip:15} MASK 255.255.255.255 {gateway} :: {domain}"
        }
    }
    args = args()
    args.os = os[args.os]
    config   = yaml.load(open(args.conf).read(), Loader=Loader)
    domains  = config["domains"]
    gateway  = config["gateway"]
    create_routes(os=args.os, domains=domains, gateway=gateway)
    if args.update:
        update_routes(os=args.os, router=args.router, password=args.password)