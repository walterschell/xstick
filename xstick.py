import serial
import time
import io
newline = '\r'
def decode_association_indication(value):
   messages = [
       'Success',
       'Active Scan Timeout',
       'Active Scan found no PANs',
       'Found PAN, but Coordinator Allow Association bit not set',
       'Found PAN, not configured for beacons',
       'Found PAN, PANID does not match',
       'Found PAN, CH does not match',
       'Energy Scan Timout',
       ' hCoordinator start request failed',
       'Invalid Coordinator Parameter',
       'Coordinator Realignment in progress',
       'Association Request not sent',
       'Association Request timed out, no reply recieved',
       'Association Request had and invalid parameter',
       'Request not transmitted, channel busy',
       'Coordinator did not ack association request',
       'association requests acked by other than coordinator',
       'Reserved',
       'Lost synchronization with coordinator',
       'Disassociated'
   ]
   if value >= len(messages):
       return 'UNKNOWN'
   return messages[value]
class PanDescriptor:
    def __init__(self, lines):
        if len(lines) < 11:
            raise Exception('Not Enough Lines')
        self.coord_address = int(lines[0], 16)
        self.coord_pan_id = int(lines[1],16)
        self.coord_addr_mode = int(lines[2], 16)
        self.channel = int(lines[3], 10)
        self.security_use = int(lines[4], 16)
        self.acl_entry = int(lines[5], 16)
        self.security_failure = int(lines[6], 16)
        self.subframe_spec = int(lines[7], 16)
        self.gts_permit = int(lines[8], 16)
        self.rssi = int(lines[9], 16)
        self.timestamp = int(lines[10], 16)
    def is_association_permitted(self):
        return 0 != (self.subframe_spec & (1 << 15))
    def coord_addr_mode_str(self):
        if self.coord_addr_mode == 0x2:
            return '16 bit short addr'
        if self.coord_addr_mode == 0x3:
            return '64 bit long addr'
        return 'UNK'
    def is_pan_coordinator(self):
        return 0 != (self.subframe_spec & (1 << 14))
    def __str__(self):
        result = ''
        result +=   'Coordinator Address: %x' % self.coord_address
        result += '\nCoordinator PAN ID: %x' % self.coord_pan_id
        result += '\nCoordinator Address Mode: %x (%s)' % (self.coord_addr_mode, self.coord_addr_mode_str())
        result += '\nChannel: %d' % self.channel
        result += '\nSecurity Use: %x' % self.security_use
        result += '\nACL Entry: %x' % self.acl_entry
        result += '\nSecurity Failure: %x' % self.security_failure
        result += '\nSubframe Spec: %x' % self.subframe_spec
        result += '\n-Association Permitted: %s' % self.is_association_permitted()
        result += '\n-Pan Coordinator: %s' % self.is_pan_coordinator()
        result += '\nGTS Permit: %x' % self.gts_permit
        result += '\nRSSI: %d' % self.rssi
        result += '\nTimestamp: %d' % self.timestamp
        return result
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
        self.logfile = open('xstick.log', 'w')

    def send(self, data):
        self.io.write(unicode(data))
        self.logfile.write('Send: ->%s<-\n' % data)
        #Shouldn't need to do this but we do
        #for char in data:
        #    self.port.write(char)
        #    time.sleep(.01)

    def enter_command_mode(self):
        time.sleep(1)
        self.io.read()
        self.send("+++")
        self.io.flush()
        time.sleep(1)
        expected_response = 'OK'
        response = self.io.read().rstrip(newline)
        
        #import pdb; pdb.set_trace()
        if not response.endswith(expected_response):
            raise Exception('Expected != Response: ->%s<- != ->%s<-' % (expected_response, response))
    def enter_command_mode_blocking(self):
        while True:
            try:
                self.enter_command_mode()
                return
            except Exception as e:
                print 'Failed to enter command mode. Retrying'
                print e
                time.sleep(1)
                pass
    def leave_command_mode(self):
        self.send_command('CN')
    def send_command(self, cmd):
        self.send('AT%s%s' % (cmd, newline))
        time.sleep(.2)
        response = self.io.readline().rstrip(newline)
        self.logfile.write('Recv: ->%s<-\n' % response)

        return response

    def get_listing(self, cmd, timeout=0):
        old_timeout = self.port.timeout
        if timeout != 0:
            self.port.timeout = timeout
        self.send('AT%s%s' % (cmd, newline))
        lines = []
        line = self.io.readline()
        self.logfile.write('Recv: ->%s<-\n' % line)
        self.port.timeout = old_timeout
        #print '->%s<-' % line.rstrip()
        while line != '':
            lines.append(line.rstrip(newline))
            line = self.io.readline()
            self.logfile.write('Recv: ->%s<-\n' % line)

        return lines

    def get_panid(self):
        return self.send_command("ID")

    def set_panid(self, panid):
        return self.send_command("ID %04x" % panid)

    def get_channel(self):
        return self.send_command("CH")

    def set_channel(self, channel):
	    return self.send_command("CH %d" % channel)

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
        lines = self.get_listing("AS %d" %duration, 5)
        results = []
        print 'DEBUG: %s' % lines.__repr__()
        while len(lines) >= 12:
            results.append(PanDescriptor(lines))
            lines = lines[12:]
        return results

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
        return int(self.send_command('AI'), 16)


    def join_pan_descriptor(self, descriptor, coord_assosicate = False):
        print 'Setting auto associate'
        print self.set_auto_associate(False)
        print 'Setting channel'
        print self.set_channel(descriptor.channel)
        print 'Setting panid'
        print self.set_panid(descriptor.coord_pan_id)
        print 'Applying changes'
        print self.apply_changes()
        #print 'Reassociating'
        #print self.reassociate()
        print 'Exiting Command mode and sleeping'
        print self.leave_command_mode()
        time.sleep(5)
        self.enter_command_mode_blocking()
        print 'Back'
    def soft_reset(self):
        return self.send_command('FR')
    def reassociate(self):
        return self.send_command('DA')
    def set_auto_associate(self, auto_associate=True):
        bit = 0
        if auto_associate:
            bit = 1
        value = (bit << 2)
        return self.send_command('A1 %x' % value)
    def get_end_association_params(self):
        return self.send_command('A1')
    def apply_changes(self):
        return self.send_command('AC')

def main():
    xstick = XStick()
    xstick.enter_command_mode_blocking()
    print 'Executing soft reset'
    xstick.soft_reset()
    xstick.enter_command_mode_blocking()
    print 'Success!'
    print 'Firmware Version: %s' % xstick.get_firmware_version()
    print '\n'.join(xstick.get_firmware_version_verbose())
    print 'PAN ID: %s' % xstick.get_panid()
    print 'Channel: %s' % xstick.get_channel()
    print 'Set Channel: %s' % xstick.set_channel(10)
    print 'Serial: %s' % xstick.get_serial_number()
    print 'Setting to endpoint'
    print xstick.set_coordinator(False)
    print 'Is Coordinator: %s' % xstick.get_is_coordinator()
    print 'Setting 802.15.4 MAC mode'
    print xstick.enable_802_15_4_mode()
    xstick.apply_changes()
    print 'MAC Mode: %s' % xstick.get_mac_mode()
    print 'Scan Channels: %s' % xstick.get_scan_channels()
    print 'Setting name'
    print xstick.set_name('testing')
    print 'Name: %s' % xstick.get_name()
    print xstick.set_panid(0x6566)
    print xstick.set_auto_associate(False)
    print xstick.apply_changes()
    print 'Rassociating'
    print xstick.reassociate()
    print 'Leaving command mode'
    print xstick.leave_command_mode()
    #time.sleep(6)
    xstick.enter_command_mode()
    print 'Association Indication: '
    print decode_association_indication(xstick.get_association_status())
    #return
    #print 'Energy Detect'
    #print '\n'.join(xstick.get_listing('ED'))
    print 'Active Scan'
    pans = []
    while not pans:
        pans = xstick.get_active_scan()
        if len(pans) == 0:
            print 'No pans discovered'
        else:
            for pan in pans:
                print pan
                print 'Joining....'
                xstick.join_pan_descriptor(pan)
                print 'PAN ID: %s' % xstick.get_panid()
                print 'Channel: %s' % xstick.get_channel()
                print 'End device association params: %s' % xstick.get_end_association_params()
                status = xstick.get_association_status()
                print 'Association Status: '
                print decode_association_indication(status)
                while status != 0:
                    xstick.leave_command_mode()
                    time.sleep(3)
                    xstick.enter_command_mode_blocking()
                    status = xstick.get_association_status()
                    print 'Association Status: '
                    print decode_association_indication(status)
                print 'Node Discover'
                print '\n'.join(xstick.get_node_discover())
    xstick.leave_command_mode()

if __name__ == '__main__':
    main()
