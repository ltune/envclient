#~*~ encoding: UTF=8 ~*~
'''
Created on 3 cze 2014

@author: adam
'''
from threading import Thread, RLock
import serial
import time
import sys
import state



class Client(Thread):
    
    def __init__(self,adr):
        Thread.__init__(self)
        self.serial =  serial.Serial()
        self.serial.setTimeout(0)
        self.serial.baudrate = 115200
        self.serial.bytes = 8
        self.serial.parity = serial.serialutil.PARITY_NONE
        self.serial.stopbits = serial.serialutil.STOPBITS_ONE
        self.serial.port = adr
        self.serial.open()
        self.serial.setRTS(level = False)

    def run(self):
        reader = Reader(serial = self.serial)
        reader.start()
        writer = Writer(serial = self.serial)
        writer.start()
        
        
class Reader(Thread):
    '''listen on serial port'''
    
    def __init__(self, serial):
        Thread.__init__(self)
        self.serial = serial
        print "serial open for reader: ", self.serial.isOpen()
        
    def run(self):
        line = None
        while state.should_run:     
            while self.serial.inWaiting() <= 0:
                time.sleep(0.1) # sleep for 100ms before checking serial again
            with serial_lock: 
                line = self.serial.readline()
                line = line.strip()
                if len(line) > 0:
                    print line
            
            
class Writer(Thread):
    '''write from stdin to serial port'''
    
    def __init__(self, serial):
        Thread.__init__(self)
        self.serial = serial
        print "serial open for writer: ", self.serial.isOpen()
            
    def run(self):
        while state.should_run:      
            order = sys.stdin.readline()
            if order.strip() == 'exit' or  order.strip() == 'quit':
                state.should_run = False
            with serial_lock:
                self.serial.write(order)
            
serial_lock = RLock()
