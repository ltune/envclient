import ConfigParser
import sys
from main.client import Client


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise RuntimeError("Please provide configfile as first parameter")
    safe_parser = ConfigParser.SafeConfigParser({
                                                 'adr': '/dev/ttyUSB0',
                                                 'ssh_host': 'localhost',
                                                 'ssh_user': 'env',
                                                 'ssh_keypath': None,
                                                 'ssh_password': None,
                                                 'input_path': '/tmp/commands',
                                                 'output_path': '/tmp/output', 
                                                 'remote_busy_path': '/tmp/vps1',
                                                 'read_timeout': 5,
                                                 'remote_timeout': 20,
                                                 'loop_timeout': 30,
                                                 })
    safe_parser.read(sys.argv[1])
    # TODO: provide config file and ConfigurationParser instead of hardcoding
    adr = safe_parser.get('serial', 'adr')
    ssh_host = safe_parser.get('remote', 'ssh_host')
    ssh_user = safe_parser.get('remote', 'ssh_user')
    ssh_keypath = safe_parser.get('remote', 'ssh_keypath')
    ssh_password = safe_parser.get('remote', 'ssh_password')
    input_path = safe_parser.get('remote', 'input_path')
    output_path = safe_parser.get('remote', 'output_path')
    remote_busy_path = safe_parser.get('remote', 'ssh_password')
    remote_timeout = safe_parser.get('remote', 'remote_timeout', raw=True)
    read_timeout = safe_parser.get('envclient', 'read_timeout', raw=True)
    loop_timeout = safe_parser.get('envclient', 'loop_timeout', raw=True)
    client = Client(adr=adr, ssh_host=ssh_host, ssh_user=ssh_user, ssh_password=ssh_password,
                    ssh_keypath=ssh_keypath, input_path=input_path, output_path=output_path,
                    remote_busy_path=remote_busy_path, read_timeout=read_timeout, 
                    remote_timeout=remote_timeout, loop_timeout=loop_timeout)
    client.start()
