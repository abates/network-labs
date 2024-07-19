import importlib
import os

from jinja2 import Environment, FileSystemLoader
import yaml

from . import filters

class ConfigGenerator:
    """Simple tool to generate baseline configs for a lab."""
    def __init__(self, lab_dir, username, password):
        """Initialize basic lab variables."""
        self.lab_dir = os.path.normpath(lab_dir)
        self.lab_name = os.path.basename(self.lab_dir)
        self.config_dir = os.path.join(self.lab_dir, "configs")

        self.configuration = None
        try:
            module = importlib.import_module(self.lab_name, package=None)
            if hasattr(module, "Configuration"):
                self.configuration = getattr(module, "Configuration")()
        except ModuleNotFoundError:
            self.configuration = None

        self.username = username
        self.password = password
        self._parse_topology()
        self.env = Environment(loader=FileSystemLoader(self.lab_dir))
        for filter_name in filters.__all__:
            self.env.filters[filter_name] = getattr(filters, filter_name)
        self.config_template = self.env.get_template("config_template.j2")

    def _parse_topology(self):
        self.devices = {}
        with open(os.path.join(self.lab_dir, f"{self.lab_name}.clab.yml")) as file:
            self.topology = yaml.safe_load(file)

        for node in self.topology["topology"]["nodes"]:
            if self.configuration:
                loopback_address = next(self.configuration.loopback_addresses)
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
            for a, b in [[0, 1], [1, 0]]:
                node_a, interface_a = link["endpoints"][a].split(":")
                node_b, interface_b = link["endpoints"][b].split(":")
                if self.configuration:
                    interface_a = self.configuration.get_interface_name(interface_a)
                    interface_b = self.configuration.get_interface_name(interface_b)

                if interface_a not in self.devices[node_a]["interfaces"]:
                    self.devices[node_a]["interfaces"][interface_a] = {
                        "name": interface_a,
                        "destination": node_b,
                        "destination_interface": interface_b,
                    }
                    if self.configuration:
                        interface_config = self.configuration.get_interface_config(node_a, interface_a, node_b, interface_b)
                        self.devices[node_a]["interfaces"][interface_a].update(interface_config)

    def _write_device_config(self, device):
        config = {**self.devices[device]}
        interface_names = sorted(config["interfaces"].keys())
        config["interfaces"] = [config["interfaces"][name] for name in interface_names]
        with open(os.path.join(self.config_dir, f"{device}.txt"), "w") as file:
            print(self.config_template.render(config), file=file)

    def build_configs(self):
        """Generate the base config files and write them."""
        for device in self.devices:
            self._write_device_config(device)
