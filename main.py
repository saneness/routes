import argparse
import yaml
import subprocess
import re
from yaml.loader import Loader

TEMPLATE = {
    "keenetic": {
        "extension": ".keenetic",
        "template" : "ip route {ip:15} {gateway}"
    },
    "windows" : {
        "extension": ".bat",
        "template" : "route ADD {ip:15} MASK 255.255.255.255 {gateway} :: {domain}"
    },
    "linux"   : {
        "extension": ".sh",
        "template" : "route add -host {ip:15} gw {gateway}"
    }
}

def args():
    parser   = argparse.ArgumentParser(description="Generate and/or update routes.")
    parser.add_argument("-c", "--conf", metavar="\b", default="config.yml", help="Path to configuration file with a gateway and domains (default: routes.yml)")
    parser.add_argument("-o", "--os", metavar="\b", default="keenetic", help="One of the operating systems: keenetic, windows, linux (default: keenetic)")
    parser.add_argument("-u", "--update", action="store_true", help="Use this flag to update routes on a router")
    parser.add_argument("-r", "--router", metavar="\b", default="admin@192.168.1.1", help="Hostname or ip address to update routes on (default: admin@192.168.1.1)")
    parser.add_argument("-p", "--password", metavar="\b", help="Password in case it required on the host")
    return parser.parse_args()

def routes(os, domains, gateway, update, router, password):
    ip_regex = re.compile("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    os = TEMPLATE[os]
    routes = []
    for domain in domains:
        ips = list(filter(ip_regex.match, [str(item)[2:-1] for item in subprocess.check_output(["dig", "+short", domain]).split()]))
        for ip in ips:
            route = eval(f'f"{os["template"]}"')
            routes.append(route)    
    open("routes" + os["extension"], "w+").write("\n".join(routes))
    routes = open("routes" + os["extension"]).read().split('\n')
    if update:
        for route in routes:
            if password:
                cmd = f"sshpass -p {password} ssh {router} {route}".split()
            else:
                cmd = f"ssh {router} {route}".split()
            subprocess.call(cmd)

if __name__ == '__main__':
    args = args()
    config   = yaml.load(open(args.conf).read(), Loader=Loader)
    domains  = config["domains"]
    gateway  = config["gateway"]
    routes(os=args.os, domains=domains, gateway=gateway, update=args.update, router=args.router, password=args.password)