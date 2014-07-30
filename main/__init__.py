from main.client import Client

if __name__ == '__main__':
    # TODO: provide config file and ConfigurationParser instead of hardcoding
    client = Client(adr='/dev/ttyUSB0', ssh_host='debian-lt', ssh_user='test2', ssh_password=None, 
           ssh_keypath='/home/test1/.ssh/id_rsa', input_path='/tmp/commands', 
           output_path='/tmp/out22', read_timeout=5, remote_timeout=20)
    client.start()