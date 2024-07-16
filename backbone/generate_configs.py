#!/usr/bin/env python3
"""Basic configuration generator for the lab."""

import base64
import hashlib
import os
import sys

from jinja2 import Environment

from netaddr import IPNetwork
import yaml

LAB_PREFIX="10.0.0.0/15"
LAB_BASE_DIR=os.path.dirname(__file__)
LAB_CONFIG_DIR=os.path.join(LAB_BASE_DIR, "configs")

template_str = """
!{% for login in auth %}
username {{ login.username }} privilege 15 secret {{ login.password }}
{% endfor %}!
hostname {{ hostname }}
!{% for interface in interfaces %}
interface {{ interface.name }}
    description "To {{ interface.destination }} {{ interface.destination_interface }}"
    no switchport
    ip address {{ interface.address }}
!{% endfor %}
interface Loopback0
   ip address {{ loopback.address }}
!
ip routing
!
router ospf 1
   router-id {{ router_id }}
   network 10.0.0.0/15 area 0.0.0.0
"""

class ConfigGenerator:
    """Simple tool to generate baseline configs for the lab."""
    def __init__(self):
        """Initialize basic lab variables."""
        self.username = os.environ.get("NAUTOBOT_NAPALM_USERNAME", None)
        self.password = os.environ.get("NAUTOBOT_NAPALM_PASSWORD", None)

        if not self.username or not self.password:
            print("The lab requires a username and password to function. Both", file=sys.stderr)
            print("    NAUTOBOT_NAPALM_USERNAME and NAUTOBOT_NAPALM_PASSWORD.", file=sys.stderr)
            print("    are required to be set in the creds.env for the lab to", file=sys.stderr)
            print("    function", file=sys.stderr)
            exit(1)

        self.lab_prefix = IPNetwork(LAB_PREFIX)
        self.loopback_prefixes, self.p2p_prefixes = list(self.lab_prefix.subnet(16, 2))
        self.loopback_prefixes = self.loopback_prefixes.subnet(32)
        self.p2p_prefixes = self.p2p_prefixes.subnet(31)

        self._parse_topology()
        self.env = Environment()
        self.config_template = self.env.from_string(template_str)

    def _parse_topology(self):
        self.devices = {}
        with open(os.path.join(LAB_BASE_DIR, "backbone.clab.yml")) as file:
            self.topology = yaml.safe_load(file)

        for node in self.topology["topology"]["nodes"]:
            loopback_address = next(self.loopback_prefixes)
            self.devices[node] = {
                "hostname": node,
                "auth": [
                    {"username": self.username, "password": self.password},
                ],
                "loopback": {
                    "address": str(loopback_address),
                },
                "router_id": str(loopback_address.ip),
                "interfaces": {}
            }

        for link in self.topology["topology"]["links"]:
            link_prefix = next(self.p2p_prefixes)
            addresses = [
                str(link_prefix),
                str(str(link_prefix.ip + 1) + "/" + str(link_prefix.prefixlen)),
            ]
            for a, b in [[0, 1], [1, 0]]:
                node_a, interface_a = link["endpoints"][a].split(":")
                node_b, interface_b = link["endpoints"][b].split(":")
                interface_a = interface_a.replace("eth", "Ethernet")
                interface_b = interface_b.replace("eth", "Ethernet")

                if interface_a not in self.devices[node_a]["interfaces"]:
                    self.devices[node_a]["interfaces"][interface_a] = {
                        "name": interface_a,
                        "destination": node_b,
                        "destination_interface": interface_b,
                        "address": addresses[a],
                    }
    
    def _write_device_config(self, device):
        config = {**self.devices[device]}
        interface_names = sorted(config["interfaces"].keys())
        config["interfaces"] = [config["interfaces"][name] for name in interface_names]
        with open(os.path.join(LAB_CONFIG_DIR, f"{device}.txt"), "w") as file:
            print(self.config_template.render(config), file=file)

    def build_configs(self):
        """Generate the base config files and write them."""
        for device in self.devices:
            self._write_device_config(device)

if __name__ == "__main__":
    if (
        not os.environ.get("NAUTOBOT_NAPALM_USERNAME", None)
        or not os.environ.get("NAUTOBOT_NAPALM_PASSWORD", None)
    ):
        print("The lab requires that both NAUTOBOT_NAPALM_USERNAME and NAUTOBOT_NAPALM_PASSWORD are set in the creds.env file")
        exit(1)


    generator = ConfigGenerator()
    generator.build_configs()
