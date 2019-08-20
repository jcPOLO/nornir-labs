from nornir.plugins.tasks import networking, text
from nornir.core.inventory import ConnectionOptions
from nornir.core.exceptions import NornirSubTaskError
from ipdb import set_trace
import main


def get_facts(nr):
    r = nr.run(task=networking.napalm_get, getters=["facts"]).result
    nr.host["facts"] = r['facts']


def get_interfaces_status(nr):
    ssh = True
    r = ''
    main.session_log(nr)
    try:
        r = nr.run(task=networking.netmiko_send_command,
                   name=f'Issue show interfaces status por SSH en {nr.host}',
                   command_string='show interfaces status',
                   use_textfsm=True
                   ).result

    except NornirSubTaskError:
        print('Al parecer, SSH no funca asi que cerrando conexion....')
        ssh = False
        try:
            nr.host.close_connections()
        except ValueError:
            print('... y abriendo un telnet rico...')
            pass

    if not ssh:

        nr.host.connection_options['netmiko'] = ConnectionOptions(
            extras={"device_type": 'cisco_ios_telnet'}
        )

        host_info = main.get_device_info(nr)

        nr.host.connection_options['netmiko'] = ConnectionOptions(
            extras={"device_type": 'cisco_ios_telnet', "session_log": main.session_log(nr)}
        )

        r = nr.run(task=networking.netmiko_send_command,
                   name=f'Hace un show interfaces status por TELNET en {nr.host}',
                   command_string='show interfaces status',
                   use_textfsm=True
                   ).result

    main.process_data_trunk(r, nr)


def basic_configuration(port, nr):
    # Transform inventory data to configuration via a template file
    r = nr.run(task=text.template_file,
               name=f"add vlan 1098 to trunk ports for {nr.host}",
               template="add_vlan.j2",
               path=f"templates/{nr.host.platform}",
               port=port)

    # Save the compiled configuration into a host variable
    nr.host["config"] = r.result

    # Deploy that configuration to the device using NAPALM
    nr.run(task=networking.netmiko_send_config,
           name=f'Haz write mem en {nr.host}',
           config_commands=nr.host["config"].splitlines())



#
#
# def send_command(port, nr):
#     interface = 'interface ' + port
#     commands = [
#         'vlan 1098', 'name anchoas', interface, 'switchport trunk allowed vlan add 1098,1099'
#     ]
#     r = nr.run(task=networking.netmiko_send_config,
#                config_commands=commands
#                )
#
#
# def get_vlans(nr):
#     r = nr.run(task=networking.netmiko_send_command,
#                name=f'hace un show vlan en {nr.host}',
#                command_string='show vlan',
#                use_textfsm=True
#                ).result
#     nr.host["vlans"] = process_data(r)
