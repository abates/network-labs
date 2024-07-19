
from collections import defaultdict
from netaddr import IPNetwork

def get_peer_ip(ip: str) -> str:
    net = IPNetwork(ip)
    if int(net.ip) % 2 == 0:
        return IPNetwork(f"{net.ip + 1}/{net.prefixlen}")
    return IPNetwork(f"{net.ip - 1}/{net.prefixlen}")

class Configuration:
    def __init__(self):
        self.lab_prefix = IPNetwork("10.0.0.0/15")
        self.loopback_addresses, self.p2p_prefixes = list(self.lab_prefix.subnet(16, 2))
        self.loopback_addresses = self.loopback_addresses.subnet(32)
        self.p2p_prefixes = self.p2p_prefixes.subnet(31)
        self.interface_configs = defaultdict(dict)

    def get_interface_name(self, interface_name: str):
        return interface_name.replace("eth", "Ethernet")

    def get_interface_config(self, device_name, interface_name, to_device_name, to_interface_name):
        if interface_name not in self.interface_configs[device_name]:
            if to_interface_name in self.interface_configs[to_device_name]:
                interface_address = str(get_peer_ip(self.interface_configs[to_device_name][to_interface_name]["address"]))
            else:
                interface_address = str(next(self.p2p_prefixes))

            self.interface_configs[device_name][interface_name] = {
                "address": interface_address,
            }
        return self.interface_configs[device_name][interface_name]
