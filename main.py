"""
arreglar que no pueda entrar por ssh por movidas de cifrado permitido

*Aug  6 20:47:26.962: %SSH-3-NO_MATCH: No matching cipher found: client chacha20-poly1305@openssh.com,aes128-ctr,aes192-ctr,aes256-ctr,aes128-gcm@openssh.com,aes256-gcm@openssh.com server aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc

(venv) 10:46:01 ~/nornir-scripts$ ssh 192.168.65.135 65003
Unable to negotiate with 192.168.65.135 port 22: no matching cipher found. Their offer: aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc

ip nat inside source static tcp 155.1.1.51 22 192.168.65.135 65001 extendable
ip nat inside source static tcp 155.1.1.52 22 192.168.65.135 65002 extendable
ip nat inside source static tcp 155.1.1.53 22 192.168.65.135 65003 extendable
ip nat inside source static tcp 155.1.1.51 23 192.168.65.135 65101 extendable
ip nat inside source static tcp 155.1.1.52 23 192.168.65.135 65102 extendable
ip nat inside source static tcp 155.1.1.53 23 192.168.65.135 65103 extendable

ssh -p 65003 -c aes128-cbc cisco@192.168.65.135
Asi conecta

ssh -Q cipher
editar /etc/ssh/sshd_config
y meter (porque dice que es los que tiene por defecto pero como que no)
Ciphers +aes128-cbc
o
Ciphers aes128-ctr,aes192-ctr,aes256-ctr,aes128-cbc,3des-cbc

The default is:

                   chacha20-poly1305@openssh.com,
                   aes128-ctr,aes192-ctr,aes256-ctr,
                   aes128-gcm@openssh.com,aes256-gcm@openssh.com,
                   aes128-cbc,aes192-cbc,aes256-cbc

             The list of available ciphers may also be obtained using "ssh -Q cipher".
Unable to negotiate with 192.168.65.135 port 22: no matching cipher found. Their offer: aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc

*Aug  7 16:50:48.404: %SSH-3-NO_MATCH: No matching cipher found: client chacha20-poly1305@openssh.com,aes128-ctr,aes192-ctr,aes256-ctr,aes128-gcm@openssh.com,aes256-gcm@openssh.com server aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc
"""

from nornir import InitNornir
from nornir.plugins.functions.text import print_result
from nornir.core.filter import F
from operator import itemgetter
from ruamel.yaml import YAML
from ipdb import set_trace
import tasks

CFG_FILE = 'config.yaml'
EXCLUDED_VLANS = [1, 1002, 1003, 1004, 1005]


def process_data(data):
    result = []

    for vlan_data in data:
        name = vlan_data["name"]
        id_ = int(vlan_data["vlan_id"])
        if id_ not in EXCLUDED_VLANS:
            vlan_dict = {
                "id": id_,
                "name": name
            }
            result.append(vlan_dict)
    return sorted(result, key=itemgetter("id"))


def get_device_info(nr):
    tasks.get_facts(nr)
    hostname = nr.host['facts']['hostname']
    os_version = nr.host['facts']['os_version']
    ip_address = nr.host.hostname
    device_dict = {
        'hostname': hostname,
        'ip_address': ip_address,
        'os_version': os_version,
    }
    return device_dict


def process_data_trunk(data, nr):
    result = []
    for interface in data:
        if interface['vlan'] == 'trunk':
            result.append(interface['port'])

    print(f'Interfaces a modificar para el cacharro {nr.host} son: {result}')
    tasks.basic_configuration(result, nr)


def session_log(nr):
    # Dynamically set the session_log to be unique per host
    # Will create output files based on nornir-name, for example "rtr1-output.txt"
    filename = f"{nr.host}-output.txt"
    # Access group object (assumes relevant group is group[0])
    group_object = nr.host.groups.refs[0]
    # Set session log at the group level
    group_object.connection_options["netmiko"].extras["session_log"] = filename
    return filename


def main() -> None:
    nr = InitNornir(config_file=CFG_FILE)
    devices = nr.filter(F(platform="ios") | F(platform="huawei"))
    result = devices.run(task=tasks.get_interfaces_status, name=f'TAREA PRINCIPAL PARA {devices.inventory.hosts}')
    print_result(result)


if __name__ == '__main__':
    main()
