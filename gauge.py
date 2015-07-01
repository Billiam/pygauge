import socket
import struct
import asyncore
import serial
import yaml
import os.path

class Sender:
    def __init__(self, serial_name):
        self.ser = serial.Serial(
            serial_name, 
            115200, 
            writeTimeout=0, 
            timeout=0, 
            parity=serial.PARITY_NONE, 
            stopbits=serial.STOPBITS_ONE
        )

    def send(self, data):
        self.ser.write(struct.pack('>cHHchcB', 'R', data['rpm'], data['max_rpm'], 'S', data['speed'], 'G', data['gear']))

class Receiver(asyncore.dispatcher):
    def __init__(self, address, sender):
        asyncore.dispatcher.__init__(self)
        self.sender = sender

        self.address = address
        self.reconnect()

    def reconnect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(self.address)

    def writable(self):
        return False

    def handle_accept(self):
        print 'accepted'

    def handle_connect(self):
        print 'connected!'

    def handle_expt(self):
        print 'exception occurred!'
        self.close()

    def readable(self):
        return True

    def handle_close(self):
        print 'closing connection'
        self.close()

    def handle_read(self):
        data = self.recv(512)

        if not data:
            return

        self.parse(data)
        
    def parse(self, data):
         # Unpack the data.
        stats = struct.unpack('64f', data[0:256])

        gear = stats[33]
        rpm = stats[37] * 10
        max_rpm = stats[63] * 10

        data = {
            'speed': int(stats[7] * 3.6 * 0.625), # mph (remove '* 0.625' for kph)
            'gear': int(stats[33]),
            'rpm': int(stats[37] * 10),
            'max_rpm': int(stats[63] * 10)
        }
        self.sender.send(data)


if __name__ == '__main__':
    try:
        approot = os.path.dirname(os.path.abspath(__file__))
    except NameError:  # We are the main py2exe script, not a module
        import sys
        approot = os.path.dirname(os.path.abspath(sys.argv[0]))

    try:
        config = yaml.load(file(approot + '/config.yml', 'r'))
    except yaml.YAMLError, exc:
        print "Error in configuration file:", exc

    arduino = Sender(config['arduino_port'])
    server = (config['telemetry_server']['host'], config['telemetry_server']['port'])
    game = Receiver(server, arduino)
    asyncore.loop()