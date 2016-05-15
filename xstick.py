import serial
import time
import io
newline = '\r'
class XStick:
    def __init__(self, filename='/dev/ttyUSB0', speed = 9600):
        self.port = serial.Serial(filename, speed)
        self.port.timeout = 1
        self.port.setDTR(value = 1)
        self.port.setRTS(value = 1)
        self.port.flushInput()
        self.io = io.TextIOWrapper(io.BufferedRWPair(self.port, self.port, 1),  
                               newline = '\r',
                               line_buffering = True)

    def send(self, data):
        self.io.write(unicode(data))
        #Shouldn't need to do this but we do
        #for char in data:
        #    self.port.write(char)
        #    time.sleep(.01)
    def enter_command_mode(self):
        time.sleep(1)
        self.send("+++")
        self.io.flush()
        time.sleep(1)
        expected_response = 'OK'
        response = self.io.readline().rstrip(newline)
        
        #import pdb; pdb.set_trace()
        if response != expected_response:
            raise Exception('Expected != Response: ->%s<- != ->%s<-' % (expected_response, response))
    def send_command(self, cmd):
        self.send('AT%s%s' % (cmd, newline))
        time.sleep(.2)
        response = self.io.readline().rstrip(newline)
        return response
    def get_listing(self, cmd):
        self.send('AT%s%s' % (cmd, newline))
        lines = []
        line = self.io.readline()
        #print '->%s<-' % line.rstrip()
        while line != '':
            lines.append(line.rstrip(newline))
            line = self.io.readline()
        return lines
    def get_panid(self):
        return self.send_command("ID")
    def get_channel(self):
        return self.send_command("CH")
    def set_channel(self, channel):
	return self.send_command("CH %s" % channel)
    def get_serial_number(self):
        return self.send_command("SH") + self.send_command("SL")
    def get_is_coordinator(self):
        return self.send_command("CE")
    def set_coordinator(self, enabled=True):
        mode = 1
        if not enabled:
            mode = 0
        return self.send_command('CE %d' % mode)
    def get_active_scan(self, duration=2):
        return self.get_listing("AS %d" %duration)
    def get_mac_mode(self):
        return self.send_command("MM")                        
    def get_node_discover(self):
        return self.get_listing("ND")
    def get_scan_channels(self):
	return self.send_command("SC")
    def get_firmware_version(self):
        return self.send_command("VR")
    def get_firmware_version_verbose(self):
        return self.get_listing("VL")
    def enable_802_15_4_mode(self, auto_ack = False):
        mode = 1
        if auto_ack:
            mode = 2
        return self.send_command('MM %d' % mode)
    def set_name(self, name):
        return self.send_command('NI %s' % name)
    def get_name(self):
        return self.send_command('NI')
    def get_association_status(self):
        return self.get_listing('AI')
def main():
    xstick = XStick()
    xstick.enter_command_mode()
    print 'Success!'
    print 'Firmware Version: %s' % xstick.get_firmware_version()
    print '\n'.join(xstick.get_firmware_version_verbose())
    print 'PAN ID: %s' % xstick.get_panid()
    print 'Channel: %s' % xstick.get_channel()
    print 'Set Channel: %s' % xstick.set_channel('10')
    print 'Serial: %s' % xstick.get_serial_number()
    print xstick.set_coordinator(False)
    print 'Is Coordinator: %s' % xstick.get_is_coordinator()
    print xstick.enable_802_15_4_mode()
    print 'MAC Mode: %s' % xstick.get_mac_mode()
    print 'Scan Channels: %s' % xstick.get_scan_channels()
    print xstick.set_name('testing')
    print 'Name: %s' % xstick.get_name()
    print 'Energy Detect'
    print '\n'.join(xstick.get_listing('ED'))
    print 'Active Scan'
    print '\n'.join(xstick.get_active_scan())
    print 'Node Discover'
    print '\n'.join(xstick.get_node_discover())
    print 'Association Status: '
    print '\n'.join(xstick.get_association_status())

if __name__ == '__main__':
    main()
