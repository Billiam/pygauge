import socket
import struct
import asyncore
import serial
import yaml
import os.path
import sys
class Sender:
    def __init__(self, serial_name):
        try:
            self.ser = serial.Serial(
                serial_name, 
                115200, 
                writeTimeout=0, 
                timeout=0, 
                parity=serial.PARITY_NONE, 
                stopbits=serial.STOPBITS_ONE
            )
        except serial.serialutil.SerialException, exc:
            sys.exit("Could not connect to serial port: %s" % serial_name)

        print "Connected to serial port: %s" % serial_name

    def send(self, data):
        self.ser.write(struct.pack('>cHHchcB', 'R', data['rpm'], data['max_rpm'], 'S', data['speed'], 'G', data['gear']))

class Receiver(asyncore.dispatcher):
    def __init__(self, address, sender, speed_units):
        asyncore.dispatcher.__init__(self)
        self.sender = sender
        self.speed_modifier = speed_units == 'mph' and 1 or 0.625
        self.address = address
        self.reconnect()

    def reconnect(self):
        self.received_data = False

        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(self.address)
        print "Waiting for data on %s:%s" % self.address

    def writable(self):
        return False

    def handle_expt(self):
        print 'exception occurred!'
        self.close()

    def readable(self):
        return True

    def handle_read(self):
        data = self.recv(512)
        
        if not data:
            return
        
        if not self.received_data:
            self.received_data = True
            print "Receiving data on %s:%s" % self.address

        self.parse(data)
        
    def parse(self, data):
         # Unpack the data.
        stats = struct.unpack('64f', data[0:256])

        gear = stats[33]
        rpm = stats[37] * 10
        max_rpm = stats[63] * 10

        data = {
            'speed': int(stats[7] * 3.6 * self.speed_modifier),
            'gear': int(stats[33]),
            'rpm': int(stats[37] * 10),
            'max_rpm': int(stats[63] * 10)
        }
        self.sender.send(data)


if __name__ == '__main__':
    if getattr(sys, 'frozen', None):
        approot = os.path.dirname(sys.executable)
    else:
        approot = os.path.dirname(os.path.realpath(__file__))

    try:
        config = yaml.load(file(approot + '/config.yml', 'r'))
    except yaml.YAMLError, exc:
        print "Error in configuration file:", exc

    arduino = Sender(config['arduino_port'])
    server = (config['telemetry_server']['host'], config['telemetry_server']['port'])
    speed_units = config['speed_units']

    game = Receiver(server, arduino, speed_units)
    asyncore.loop()
