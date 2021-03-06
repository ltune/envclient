#~*~ encoding: UTF=8 ~*~
'''
Created on 3 cze 2014

@author: adam
'''
from threading import Thread, RLock
import serial
import time
import paramiko
import sys
import state


CLIENT_PREFIX_COMMAND = 'envclient'
CLIENT_DELIMITER = '~'
CLIENT_STOP = "stop"
CLIENT_LOOP = 'loop'

class Client(Thread):
    
    def __init__(self, adr, ssh_host, ssh_user, ssh_password, ssh_keypath, input_path, output_path, 
                 remote_busy_path, read_timeout=10, remote_timeout=20, loop_timeout=60):
        Thread.__init__(self)
        self.input_path = input_path
        self.output_path = output_path
        self.remote_busy_path = remote_busy_path
        self._ssh_host = ssh_host
        self._ssh_user = ssh_user
        self._ssh_password = ssh_password
        self._ssh_keypath = ssh_keypath 
        self._serial =  serial.Serial()
        self._ssh_user = ssh_user
        self.read_timeout = read_timeout # time for reader to capture answers
        self.remote_timeout = remote_timeout # timeout to retry remote sync
        self.loop_timeout = loop_timeout # timeout to restart overall process
        self._must_wait = True # used for syncronization
        self._enabled = True # to keep app running
        # setup serial
        self._serial.setTimeout(0)
        self._serial.baudrate = 115200
        self._serial.bytes = 8
        self._serial.parity = serial.serialutil.PARITY_NONE
        self._serial.stopbits = serial.serialutil.STOPBITS_ONE
        self._serial.port = adr

    def run(self):
        """client main method."""
        while self._enabled:
            self._establish_remote() # open remote connection
            self._get_remote() # get commands from file at remote location
            # listen on serial port:
            self._serial.open()
            self._serial.setRTS(level = False)
            # start serial reader and writer 
            self._reader = Reader(serial = self._serial, read_timeout=self.read_timeout)
            self._reader.start()
            self._writer = Writer(serial = self._serial, commands=self.input_commands)
            self._writer.start()
            # wait for writer and reader to finish
            self._writer.join()
            self._reader.join()
            # close serial port
            self._serial.close()
            # write file contents to remote location
            self._deliver_remote() # transfer results to remote
            self._remove_input_commands() # clear processed commands
            self._free_remote() # free access on critical resources
            time.sleep(self.loop_timeout)
    
    def _setup_remote(self):
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(hostname=self._ssh_host,
                    username=self._ssh_user, 
                    password=self._ssh_password,
                    key_filename=self._ssh_keypath
                    )
        
    def _establish_remote(self):
        """Establish connection to remote location."""
        self._setup_remote()
        while not self._synced():
            # diconnect and try reconnection after remote_timeout seconds
            self._close_remote()
            time.sleep(self.remote_timeout)
            self._setup_remote()
    
    def _synced(self):
        """Get exlusive access on remote command file"""
        _stdin, stdout, _stderr = self._ssh.exec_command("cat {}".format(self.remote_busy_path))
        busy = ''.join(stdout.readlines())
        if '1' in busy:
            return False
        else:
            return True

    def _free_remote(self):
        """Free exclusive access on remote files"""
        self._ssh.close()

    def _close_remote(self):
        self._ssh.close()

    def _get_remote(self):
        _stdin, stdout, _stderr = self._ssh.exec_command("cat {}".format(self.input_path))
        commands = stdout.readlines()
        env_commands = []
        self.input_commands =  [line.replace('|r','\n').replace('\n','') for line in commands if len(line)>0]
        # remove commands that are for envclient
        j = 0
        while j < len(self.input_commands):
            if CLIENT_PREFIX_COMMAND in self.input_commands[j]:
                env_commands.append(self.input_commands[j].split(CLIENT_DELIMITER))
                del self.input_commands[j]
            else:
                j += 1
        for env_cmd in env_commands:
            if len(env_cmd) > 1 and env_cmd[1] == CLIENT_STOP:
                self._enabled = False
            elif len(env_cmd) > 2 and env_cmd[1] == CLIENT_LOOP:
                self.loop_timeout = int(env_cmd[2])

    def _deliver_remote(self):
        """Deliver results from reader to remote host."""
        sftp = self._ssh.open_sftp() 
        with sftp.open(self.output_path, 'a+b') as f:
            f.write('\n'.join(self._reader.lines))

    def _remove_input_commands(self):
        """Clear commands after successfull reading."""
        sftp = self._ssh.open_sftp()
        with sftp.open(self.input_path, 'wb') as f:
            f.write('')


class Reader(Thread):
    '''listen on serial port'''
    
    def __init__(self, serial, read_timeout):
        Thread.__init__(self)
        self._serial = serial
        self.read_timeout = read_timeout # read timeout in sec
        
    def run(self):
        line = None
        term_time = time.time() + self.read_timeout
        self.lines = []
        while time.time() < term_time:
            while self._serial.inWaiting() <= 0 and time.time() < term_time:
                time.sleep(0.1) # sleep for 100ms before checking serial again
            with serial_lock: 
                line = self._serial.readline()
                line = line.strip()
                if len(line) > 0:
                    self.lines.append(line)


class Writer(Thread):
    '''write from stdin to serial port'''
    
    def __init__(self, serial, commands=None):
        Thread.__init__(self)
        self._serial = serial
        self.commands = commands or []
            
    def run(self):
        for command in self.commands:
            time.sleep(0.2) # sleep for 200ms before checking serial again
            with serial_lock:
                self._serial.write(str(command)+'\n')
            
serial_lock = RLock()
