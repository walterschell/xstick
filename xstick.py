import serial
import time
import io
newline = '\r'
class XStick:
    def __init__(self, filename='/dev/ttyUSB0', speed = 9600):
        self.port = serial.Serial(filename, speed)
        self.port.setTimeout(1)
        self.port.setDTR(level = True)
        self.port.setRTS(level = True)
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
    def get_serial_number(self):
        return self.send_command("SH") + self.send_command("SL")
    def get_is_coordinator(self):
        return self.send_command("CE")
    def get_active_scan(self, duration=2):
        return self.get_listing("AS %d")
                            
def main():
    xstick = XStick()
    xstick.enter_command_mode()
    print 'Success!'
    print 'PAN ID: %s' % xstick.get_panid()
    print 'Channel: %s' % xstick.get_channel()
    print 'Serial: %s' % xstick.get_serial_number()
    print 'Is Coordinator: %s' % xstick.get_is_coordinator()
    print 'Energy Detect'
    print '\n'.join(xstick.get_listing('ED'))
    print 'Active Scan'
    print '\n'.join(xstick.get_active_scan())
if __name__ == '__main__':
    main()