import serial
import time
import io
newline = '\r'
debug_on = False
def debug(msg):
    if debug_on:
        print msg

class XStick:
    def __init__(self, filename='/dev/ttyUSB0', speed = 9600):
        self.port = serial.Serial(filename, speed)
        self.port.timeout = None
        self.port.setDTR(value = 1)
        self.port.setRTS(value = 1)
        self.port.flushInput()
        self.io = io.TextIOWrapper(io.BufferedRWPair(self.port, self.port, 1),
                               newline = '\r',
                               line_buffering = True)
        self.cached_pan_descriptors = []
        self.cached_scan_channel_dwell = 0
        self.cached_scan_channels = 0
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
    def exit_command_mode(self):
        self.send_command('CN')
    def send_command(self, cmd):
        self.send('AT%s%s' % (cmd, newline))
        time.sleep(.2)
        response = self.io.readline().rstrip(newline)
        return response
    def get_listing(self, cmd):
        self.send('AT%s%s' % (cmd, newline))
        lines = []
        line = self.io.readline().rstrip()
        debug('->%s<-' % line.rstrip())
        while line != '' and line != 'ERROR':
            lines.append(line.rstrip(newline))
            line = self.io.readline().rstrip()
            debug('->%s<-' % line.rstrip())
        return lines
    def get_panid(self):
        return self.send_command("ID")
    def set_panid(self, panid):
        return self.send_command('ID %x' % panid)
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
    def get_active_scan(self, duration=5):
        lines = self.get_listing("AS %d" %duration)
        self.cached_pan_descriptors = []
        spot = 0
        while len(lines) - spot >= 11:
            self.cached_pan_descriptors.append(PanDescriptor(lines[spot:spot + 11]))
            spot += 11
        return lines
    def get_mac_mode(self):
        return self.send_command("MM")
    def get_node_discover(self):
        return self.get_listing("ND")
    def get_scan_channels(self):
	result = self.send_command("SC")
        self.cached_scan_channels = int(result, 16)
        return result
    def decode_scan_channels(self):
        result = []
        channel_base = 0xb
        for i in range(16):
            if self.cached_scan_channels & (1 << i):
                result.append(channel_base + i)
        return result
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
        return self.send_command('AI')
    def get_scan_duration(self):
        duration = self.send_command('SD')
        self.cached_channel_dwell = (2 ** int(duration,16)) * 15.36
        return duration
    def set_scan_duration(self, new_sd = 8):
        return self.send_command('SD %x' % new_sd)
    def apply_changes(self):
        return self.send_command('AC')
    def energy_detect(self, decode = True):
        lines = self.get_listing('ED')
        if not decode:
            return lines
        lines = map(lambda x: '-%d dBm' % int(x, 16), lines)
        if not len(lines) == len(self.decode_scan_channels()):
            return lines
        for i in range(len(lines)):
            lines[i] = '%d: %s' % (self.decode_scan_channels()[i], lines[i])
        return lines
    def attempt_join(self, descriptor):
        self.set_panid(int(descriptor.CoordPanID, 16))
        self.set_channel(descriptor.Channel)
        self.send_command('A1 4')

class PanDescriptor:
    def __init__(self, lines):
        if len(lines) != 11:
            raise Exception('Wrong number of lines')
        self.CoordAddress = lines[0]
        self.CoordPanID = lines[1]
        self.CoordAddrMode = lines[2]
        self.CoordAddrModeString = 'UNK Mode'
        if self.CoordAddrMode == '02':
            self.CoordAddrModeString = '16 bit Short Address'
        elif self.CoordAddrMode == '03':
            self.CoordAddrModeString = '64 bit Long Address'
        self.ChannelStr = lines[3]
        self.Channel = int(self.ChannelStr, 16)
        self.SecurityUse = lines[4]
        self.ACLEntry = lines[5]
        self.SecurityFailure = lines[6]
        self.SuperFrameSpecString = lines[7]
        self.SuperFrameSpec = int(lines[7], 16)
        self.GtsPermit = lines[8]
        self.RSSI = lines[9]
        self.TimeStamp = lines[10]

    def decode_super_frame_spec(self):
        result = []
        framespec = self.SuperFrameSpec
        if framespec & 1:
            result.append('Association Permitted')
        else:
            result.append('Associattion NOT permitted')
        if framespec & (1 << 1):
            result.append('PAN Coordinator')
        else:
            result.append('NOT PAN Coordinator')

        return map(lambda x: '* %s' % x, result)
    def __str__(self):
        result = []
        result.append('Timestamp: %s' % self.TimeStamp)
        result.append('Pan ID: %s' % self.CoordPanID)
        result.append('Coord Address: %s' % self.CoordAddress)
        result.append('Coord Addr Mode: %s (%s)' % (self.CoordAddrModeString, self.CoordAddrMode))
        result.append('Channel: 0x%s (%d)' % (self.ChannelStr, self.Channel))
        result.append('RSSI: -%s dBm' % self.RSSI)
        result.append('Security Use: %s' % self.SecurityUse)
        result.append('ACLEntry: %s' % self.ACLEntry)
        result.append('SecurityFailure: %s' % self.SecurityFailure)
        result.append('SuperFrameSpec: %s' % self.SuperFrameSpecString)
        result += self.decode_super_frame_spec()
        result.append('Gts Permit: %s' % self.GtsPermit)
        return '\n'.join(result)

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
    print 'Scan Channels: %s (%s)' % (xstick.get_scan_channels(), xstick.decode_scan_channels())
    print 'Scan Duration: %s' % xstick.get_scan_duration()
    print 'Channel Dewll: %0.2f ms' % xstick.cached_channel_dwell
    #print 'Setting Scan duration to 8: %s' % xstick.set_scan_duration(12)
    #print 'Scan Duration: %s' % xstick.get_scan_duration()
    #print 'Channel Dewll: %0.2f ms' % xstick.cached_channel_dwell
    print xstick.set_name('testing')
    print 'Aplying changes... %s' % xstick.apply_changes()
    print 'Name: %s' % xstick.get_name()
    print 'Energy Detect'
    print '\n'.join(xstick.energy_detect())
    print 'Active Scan'
    print '\n'.join(xstick.get_active_scan(6))
    print 'Node Discover'
    print '\n'.join(xstick.get_node_discover())
    print 'Association Status: %s' % xstick.get_association_status()
    for descriptor in xstick.cached_pan_descriptors:
        print '*** Pan Descriptor ***'
        print descriptor
        print

    logfile_path = '/tmp/xstick.log'
    print 'Entering scanning loop'
    print 'tail -f %s' % logfile_path
    with open(logfile_path, 'a') as fh:
        while True:
            fh.write('--- %s ---\n' % time.asctime())
            print 'Scanning...',
            xstick.get_active_scan(6)
            print 'Done!'
            for descriptor in xstick.cached_pan_descriptors:
                fh.write('*** Pan Descriptor ***\n')
                fh.write(str(descriptor))
                fh.write('\n')
if __name__ == '__main__':
    main()
