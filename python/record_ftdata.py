#! /sw/bin/python2.7

# RV-8 data collection script
#
# Spawns a separate thread for each device.
# Records a separate data file for each device.  The data files can be 
# post-processed to merge them, using the script merge_ftdata.py.
# 
# Has a class for each of EIS 4000, D10A EFIS, GNS 430 and discretes.
# Each class is defined in a separate module.
# Will eventually use a Tkinter GUI to select which devices to use (default of 
# all), and to start/stop the recording.
#

# STATUS - Extensive testing done on 26 Mar, using the  following file versions
#          (svn version numbers):
#
#               293      293 kwh          gns430.py
#               289      282 kwh          test.py
#               293      293 kwh          eis4000.py
#               293      293 kwh          d10a.py
#               293      293 kwh          discretes.py
#
#          The testing involved starting the script, waiting several minutes,
#          then powering up the devices.  The EIS and GNS were both depowered
#          for a short period, then repowered (as may happen during engine
#          start).  A GNS flight plan was loaded, OBS and direct-to were
#          functioned.  All data matched the log, except that the EIS module
#          records every record for a long period after the EIS starts sending
#          data.  Changed the EIS timeout, and this problem seems to be fixed.


# TO DO - SOMEDAY - Items that do not affect the required functionality
#
#       1. Add GUI to select serial ports, as the exact name varies on each
#          computer.
#
#       2. Add code to test for USB plugged into wrong port (gives different
#          ports).
#
#       3. Instead of To Do 1 or 2, could add code to find the correct ports,
#          and automatically assign them.
#
#       4. Add code to load the data parametre scaling from the class files.
#          Currently the scaling is hard coded in the parse function in each 
#          class file.
#
#       5. Add code to gracefully stop recording, upon command.  The threads 
#          have such a hook now, but need the user interface.
#
#       6. Done.
#
#       7. Fixed.
#
# DONE  1. Initial tests show that the script freezes if
#          EFIS or GNS data is interrupted.  Need more testing to find the
#          problem.  The script does not hang if the EIS is turned off.  What 
#          is the difference between the EIS and the other devices?  Note: the 
#          script comes back to life if the EFIS or GNS is turned back on, so
#          this may not be a critical bug.  Power interruptions seem to allow
#          it to recover.  The only issue would be at the end of the flight, if
#          it was desired to power down the aircraft first.
#
#          Fixed on 21 Mar 06, SVN version 279.
#
#       5. Add code to gracefully stop recording, upon command.  The threads 
#          have such a hook now, but need the user interface.
#
#          Partially implemented.  Can stop the script by having another
#          terminal do a "touch stop_recording.flag".
#
#       6. Add code to provide some visual feedback that the script is 
#          continuing to work.
#
#          Added a print from each module once per cycle.
#
#       7. Fix data rate after start up.  If the script is started before the
#          the devices are sending data, there is a backlog of expected data
#          records.  Once the devices start sending data, the script grabs data
#          as fast as possible until it makes up the backlog.  The recorded 
#          data shows a bunch of records with very short times between them.
#
#         Fixed by reducing the timeout for the EIS and EFIS, so the script
#         wasn't pausing for one second at each read attempt.
#
#      1. Write a script to post-process the data files to combine them into
#         one file.  Or, write code to do that on the fly, during the data
#        recording.


# Future code cleanup ideas:
#       1. Move all of the code in each module under the class definition.
#          Then can standardize the grab data function names, and call them
#          from a loop, rather than as individual lines.
#
#       2. Use the __import__ built-in function to call the modules (see Python
#          Cookbook recipe 16.3).
#
#       3. When checking for numeric data, use try, float, except (see Python
#          Cookbook recipe 16.1).
#
#       4. Rework code to reduce the amount of string concatenation.  See:
#          http://wiki.python.org/moin/PythonSpeed/PerformanceTips


'''usage: %prog [options]
   -c, --computer: computer the script is run from: PMac or PBook.  Defaults to PBook'''

from __future__ import division
import serial
from eis4000 import *
from d10a import *
from gns430 import *
from discretes import *
import time
import threading
# import Queue
import os, os.path

if os.path.exists('stop_recording.flag'):
    os.remove('stop_recording.flag')
#------------------------------------------------------------------------------#
#
# Define and parse command line options
#
#------------------------------------------------------------------------------#
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c", "--computer", dest="computer", default="PBook",
                 help="Identify computer used, PBook or PMac. Defaults to PBook", metavar="computer")
# parser.add_option("-c", "--computer", dest="computer", default="EeePC",
#                   help="Identify computer used, EeePC, PBook or PMac. Defaults to EeePC", metavar="computer")
parser.add_option("-d", "--duration", dest="duration", default="300",
                  help="Data recording duration (minutes). Defaults to 300 (5 hours)", metavar="duration")
parser.add_option("-o", "--output", dest="output", 
                  help="Define output directory.  Default is the script directory", metavar="output directory")
parser.add_option("-r", "--rate", dest="data_rate", default="2",
                  help="Data rate in records per second. Defaults to 2 records per second", metavar="data_rate")
parser.add_option("-t", "--test", dest="test_mode", default="0",
                  help="Test mode. '0' = read from serial port. '1' = read from file for testing. Defaults to '0'", metavar="test_mode")

(options, args) = parser.parse_args()

if (options.computer not in ("PBook","PMac", "EeePC")):
   parser.error('computer must be "PBook", "PMac" or "EeePC"')

data_rate = float(options.data_rate)
duration = float(options.duration)
test_mode = options.test_mode

if options.output:
    output_dir = options.output
    print 'Output directory defined as', output_dir
else:
    output_dir = ''


#------------------------------------------------------------------------------#
#
# load_devices(list)
#
# load serial ports, using info from the modules.  One module file per device.
#
#------------------------------------------------------------------------------#
def load_devices(list):
    
    count = -1
    for item in list:
        count += 1
        if item == 'EIS4000':
            device = 'D' + str(count)
            device = EIS4000()
            
#            S0 = serial.Serial(port='/dev/tty.KeySerial1')
            if options.computer == 'PBook':
                S0 = serial.Serial(port='/dev/tty.USA49W3b1P1.1')
            elif options.computer == 'PMac':
                S0 = serial.Serial(port='/dev/tty.USA49W1b213P1.1')
            elif options.computer == 'EeePC':
                S0 = serial.Serial(port='/dev/ttyUSB0')
            else:
                print 'Computer must be "EeePC", "PBook" or "PMac"'            
            device_list.append(device)
            serial_list[item] = S0
        
        if item == 'D10A':
            device = 'D' + str(count)
            device = D10A()
            if options.computer == 'PBook':
                S1 = serial.Serial(port='/dev/tty.USA49W3b1P2.2')
            elif options.computer == 'PMac':
                S1 = serial.Serial(port='/dev/tty.USA49W1b213P2.2')
            elif options.computer == 'EeePC':
                S1 = serial.Serial(port='/dev/ttyUSB1')
            else:
                print 'Computer must be "EeePC", "PBook" or "PMac"'            
            device_list.append(device)
            serial_list[item] = S1
        
        if item == 'GNS430':
            device = 'D' + str(count)
            device = GNS430()
            if options.computer == 'PBook':
                S2 = serial.Serial(port='/dev/tty.USA49W3b1P3.3')
            elif options.computer == 'PMac':
                S2 = serial.Serial(port='/dev/tty.USA49W1b213P3.3')
            elif options.computer == 'EeePC':
                S2 = serial.Serial(port='/dev/ttyUSB2')
            else:
                print 'Computer must be "EeePC", "PBook" or "PMac"'            
            device_list.append(device)
            serial_list[item] = S2
        
        if item == 'Discretes':
            device = 'D' + str(count)
            device = Discretes()
            if options.computer == 'PBook':
                S3 = serial.Serial(port='/dev/tty.USA49W3b1P4.4')
            elif options.computer == 'PMac':
                S3 = serial.Serial(port='/dev/tty.USA49W1b213P4.4')
            elif options.computer == 'EeePC':
                S3 = serial.Serial(port='/dev/ttyUSB3')
            else:
                print 'Computer must be "EeePC", "PBook" or "PMac"'
            device_list.append(device)
            serial_list[item] = S3
            
    # load device characteristics from modules
    for device in device_list:
        serial_list[device.device_name].baudrate = device.baudrate
        serial_list[device.device_name].timeout  = device.timeout
        serial_list[device.device_name].xonxoff  = device.xonxoff
        serial_list[device.device_name].rtscts   = device.rtscts

#------------------------------------------------------------------------------#
#
# print_serial_ports()
#
# print device names and characteristics as a test.  Can be commented out.
#
#------------------------------------------------------------------------------#
def print_serial_ports():
    name_len = 10
    baud_len = 7
    port_len = 27
    byte_len = 7
    parity_len = 7
    print 'Device       baud   port                    bytes  parity  time'
    print '                                                           out'
    for device in device_list:
        print_buffer = ''
        print_buffer = device.device_name.ljust(name_len)
        print_buffer += str(serial_list[device.device_name].baudrate).rjust(baud_len) + '  '
        print_buffer += serial_list[device.device_name].port.ljust(port_len)
        print_buffer += str(serial_list[device.device_name].bytesize).ljust(byte_len)
        print_buffer += serial_list[device.device_name].parity.ljust(parity_len)
        print_buffer += str(serial_list[device.device_name].timeout)
        print print_buffer

#------------------------------------------------------------------------------#
#
# make_column_header1(device)
# make_column_header2(device)
#
# Create the two data header lines for a given device. First line has column labels.  
# Second line has units.
#
#------------------------------------------------------------------------------#
def make_column_header1(device):
    header = str(device) + ' Time\t'
    for item in device.order_label_units:
    # only put item in header it this item is in the list of items to be recorded
        if device.data_to_record[item[0]] == 1:
            header += item[1] + '\t'
    header = header[:-1]
    return header

def make_column_header2(device):
    header = '(seconds)\t'
    for item in device.order_label_units:
        if device.data_to_record[item[0]] == 1:
            header += '(' + item[2] + ')\t'
    header = header[:-1]
    return header

#------------------------------------------------------------------------------#
#
# Main script starts here
#
#------------------------------------------------------------------------------#
# list = ['Discretes']
# list = ['Discretes', 'D10A', 'EIS4000']
list = ['Discretes', 'D10A', 'EIS4000', 'GNS430']
# list = ['Discretes', 'EIS4000', 'GNS430']
# list = ['Discretes', 'D10A', 'GNS430']
# list = ['Discretes', 'D10A', 'EIS4000', 'GNS430', 'LEA4T_raw', 'LEA4T_time']

device_list = []
serial_list = {}

if test_mode == '0':
    load_devices(list)
    print_serial_ports()
else:
    print 'In test mode - reading test data from a file.'


# Open files
outputs = {}
number_list = range(4)
header_length = {}
header1 = {}
header2 = {}
blank_data = {}
data_hold = {}
for device in list:
    data_hold[device] = ''

header_len_re = re.compile(r'\t')

for (device, number) in zip (list, number_list):
    print device, number
    file_name = device + '_data-' + time.strftime('%Y-%m-%d-%H%M') + '.txt'
    if output_dir != '':
        file_name = output_dir + '/' + file_name
    outputs[device] = open(file_name, 'w')
    if device != 'LEA4T_raw':
        outputs[device].write(file_name)
        outputs[device].write('\n\n')
    if device == 'EIS4000':
        header1[device] = make_column_header1(EIS4000)
        header2[device] = make_column_header2(EIS4000)
        header = header1[device] + '\n' + header2[device] + '\n'
    elif device == 'D10A':
        header1[device] = make_column_header1(D10A)
        header2[device] = make_column_header2(D10A)
        header = header1[device] + '\n' + header2[device] + '\n'
    elif device == 'GNS430':
        header1[device] = make_column_header1(GNS430)
        header2[device] = make_column_header2(GNS430)
        header = header1[device] + '\n' + header2[device] + '\n'
    elif device == 'LEA4T_time':
        header1[device] = make_column_header1(LEA4T)
        header2[device] = make_column_header2(LEA4T)
        header = header1[device] + '\n' + header2[device] + '\n'
    elif device == 'LEA4T_raw':
        # no headers for raw data file.  Record nothing but raw data
        pass
    else:
        header1[device] = make_column_header1(Discretes)
        header2[device] = make_column_header2(Discretes)
        header = header1[device] + '\n' + header2[device] + '\n'

    if device != 'LEA4T_raw':
        # no headers for raw data file.  Record nothing but raw data
        outputs[device].write(header)
        header_length[device] = (len(header_len_re.findall(header)) // 2) + 1
        blank_data[device] = '\t' * header_length[device] + '\n'


# set up threads
class EFIS_thread(threading.Thread):
    def run(self):
        grab_efis_data(test_mode, data_rate, duration, serial_list, outputs, )

class EIS_thread(threading.Thread):
    def run(self):
        grab_eis_data(test_mode, data_rate, duration, serial_list, outputs, )

class GNS_thread(threading.Thread):
    def run(self):
        grab_gns_data(test_mode, data_rate, duration, serial_list, outputs, )

class Discretes_thread(threading.Thread):
    def run(self):
        grab_discrete_data(test_mode, data_rate, duration, serial_list, outputs, )

class LEA4T_thread(threading.Thread):
    def run(self):
        grab_lea4t_data(test_mode, data_rate, duration, serial_list, outputs, )

# start threads
if 'Discretes' in list:
    Discretes_thread().start()

if 'D10A' in list:
    EFIS_thread().start()

if 'EIS4000' in list:
    EIS_thread().start()

if 'GNS430' in list:
    # GPS outputs one record per second, so there is no need to try to use a 
    # higher data rate. if a higher data rate is selected, switch to one per 
    # second for the GPS.
    if data_rate > 1:
        data_rate_temp = 1
        (data_rate, data_rate_temp) = (data_rate_temp, data_rate)
        GNS_thread().start()
        (data_rate, data_rate_temp) = (data_rate_temp, data_rate)
    else:
        GNS_thread().start()

# if 'Discretes' in list:
#     Discretes_thread().start()
# 
if 'LEA4T' in list:
    LEA4T_thread().start()

# print tell tale, to let us know it is still alive.
count = 0
while 1:
    time.sleep(1)
    print '*', count
    count += 1
    if os.path.exists('stop_recording.flag'):
        print 'Data recording stopping within 20 seconds.'
        time.sleep(20)
        break
