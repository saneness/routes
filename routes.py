from yaml import load
from yaml.loader import Loader
from subprocess import check_output
from re import compile

config = load(open("routes.yml").read(), Loader=Loader)

open("routes.bat", "w+").write("\n".join(["\n".join([f"route ADD {ip:15} MASK 255.255.255.255 {config['gateway']} :: {domain}" for ip in list(filter(compile("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$").match, [str(item)[2:-1] for item in check_output(["dig", "+short", domain]).split()]))]) for domain in config["domains"]]))