#! /sw/bin/python2.4

# Proof of concept for RV-8 data collection - working for EIS, EFIS and GNS.
# Tested on the aircraft, recording data from all three, on 12 Mar 06.
#
# Spawns a separate thread for each device.
# Records a separate data file for each device.
# 
# Has a class for each of EIS 4000, D10A EFIS, GNS 430 and discretes.
# Each class is defined in a separate module.
# Will eventually use a Tkinter GUI to select which devices to use (default of 
# all), and to start/stop the recording.

# Probably need to use a separate thread for each serial port.
# Probably want to keep each port's thread going for the whole duration, to
# avoid the overhead of opening and closing serial ports.  Might be able to use
# the queue module to allow threads to feed their results back to the main
# process.

# STATUS - The merging of data from the device queues seems to work, but it
#          uses way too much CPU time - 65 to 90%.  Uses 20 to 25% CPU time
#          data merging.  Give up on real time merging, and make a post-flt
#          merge program. (sleep added in v285, which brings the CPU useage
#          20 - 25%).  Seems to work at first glance, but need more testing.
#          
#          EIS out stops the display.  Does the data recording stop for all
#          devices?
#
#          Blank device lines may be one field too long.

# TO DO - CRITICAL - Before using scripts for recording data
#
#       1. Write a script to post-process the data files to combine them into
#          one file.  Or, write code to do that on the fly, during the data
#          recording.
#
# 
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
#       4. Add code to load the data parametre info from the class files:
#          which ones to record, the order, label and scaling.
#
#       5. Add code to gracefully stop recording, upon command.  The threads 
#          have such a hook now, but need the user interface.
#
#       6. Add code to provide some visual feedback that the script is 
#          continuing to work.
#
#       7. Fix data rate after start up.  If the script is started before the
#          the devices are sending data, there is a backlog of expected data
#          records.  Once the devices start sending data, the script grabs data
#          as fast as possible until it makes up the backlog.  The recorded 
#          data shows a bunch of records with very short times between them.
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



'''usage: %prog [options]
   -c, --computer: computer the script is run from: PMac or PBook.  Defaults to PBook'''

import serial
from eis4000 import *
from d10a import *
from gns430 import *
from discretes import *
import time
import threading
import Queue
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
parser.add_option("-d", "--duration", dest="duration", default="300",
                  help="Data recording duration (minutes). Defaults to 300 (5 hours)", metavar="duration")
parser.add_option("-o", "--output", dest="output", 
                  help="Define output directory.  Default is the script directory", metavar="output directory")
parser.add_option("-r", "--rate", dest="data_rate", default="2",
                  help="Data rate in records per second. Defaults to 2 records per second", metavar="data_rate")
parser.add_option("-t", "--test", dest="test_mode", default="0",
                  help="Test mode. '0' = read from serial port. '1' = read from file for testing. Defaults to '0'", metavar="test_mode")

(options, args) = parser.parse_args()

if (options.computer not in ("PBook","PMac")):
   parser.error('computer must be "PBook" or "PMac"')

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
			
			S0 = serial.Serial(port='/dev/tty.KeySerial1')
			device_list.append(device)
			serial_list[item] = S0
		
		if item == 'D10A':
			device = 'D' + str(count)
			device = D10A()
			if options.computer == 'PBook':
				S1 = serial.Serial(port='/dev/tty.USA49W3b1P2.2')
			elif options.computer == 'PMac':
				S1 = serial.Serial(port='/dev/tty.USA49W1b213P2.2')
			else:
				print 'Computer must be "PBook" or "PMac"'
			device_list.append(device)
			serial_list[item] = S1
		
		if item == 'GNS430':
			device = 'D' + str(count)
			device = GNS430()
			if options.computer == 'PBook':
				S2 = serial.Serial(port='/dev/tty.USA49W3b1P3.3')
			elif options.computer == 'PMac':
				S2 = serial.Serial(port='/dev/tty.USA49W1b213P3.3')
			else:
				print 'Computer must be "PBook" or "PMac"'
			device_list.append(device)
			serial_list[item] = S2
		
		if item == 'Discretes':
			device = 'D' + str(count)
			device = Discretes()
			if options.computer == 'PBook':
				S3 = serial.Serial(port='/dev/tty.USA49W3b1P4.4')
			elif options.computer == 'PMac':
				S3 = serial.Serial(port='/dev/tty.USA49W1b213P4.4')
			else:
				print 'Computer must be "PBook" or "PMac"'
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
# pull_data_from_queue(window_start, window_end, device)
#
# Pull data devices from their queues and assemble into a data line.
# Poll all queues.  If the queue data is earlier than time, discard it.
# If the queue data is too new (i.e. it has a time stamp that is later than this
# block), put it in a temp variable to use it later.
#
#------------------------------------------------------------------------------#
def pull_data_from_queue(window_start, window_end, device):
# 	window_start = float(window_start)
# 	window_end = float(window_end)
	global data_hold
	data_time_stamp = 0
# 	time_flag = False
	if data_hold[device]:
		print 'In data hold loop'
		data = data_hold[device]
		data_time_stamp = float(data[:13])		
	else:
		while data_time_stamp < window_start:
			try:
				data = queues[device].get()
				data_time_stamp = float(data[:13])
				print 'In normal loop for', device, 'with data time of:', data_time_stamp
			except Empty:
				print 'In except Empty block for', device
				data = blank_data[device]
				break
	if data_time_stamp >= window_end:
		data_hold[device] = data
		data = blank_data[device]
		print 'In too late block, with data time of:', data_time_stamp
		print 'Window end is:', window_end
	else:
		data_hold[device] = ''
	# strip \n from data
	data = data[:-1]
	return data
#

# Add GUI code here to fill list with the names of the devices to use
# Allowable values are:
# EIS4000
# D10A
# GNS430
# Discretes

list = ['Discretes', 'D10A', 'EIS4000', 'GNS430']
# list = ['Discretes', 'D10A', ]

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
# for (device, number) in zip (list, number_list):
# 	print device, number
# 	file_name = device + '_data-' + time.strftime('%Y-%m-%d-%H%M') + '.txt'
# 	if output_dir != '':
# 		file_name = output_dir + '/' + file_name
# 	outputs[number] = open(file_name, 'w')
# 	outputs[number].write(file_name)
# 	outputs[number].write('\n\n')
# 	if device == 'EIS4000':
# 		header1[device] = make_column_header1(EIS4000)
# 		header2[device] = make_column_header2(EIS4000)
# 		header = header1[device] + '\n' + header2[device] + '\n'
# 	elif device == 'D10A':
# 		header1[device] = make_column_header1(D10A)
# 		header2[device] = make_column_header2(D10A)
# 		header = header1[device] + '\n' + header2[device] + '\n'
# 	elif device == 'GNS430':
# 		header1[device] = make_column_header1(GNS430)
# 		header2[device] = make_column_header2(GNS430)
# 		header = header1[device] + '\n' + header2[device] + '\n'
# 	else:
# 		header1[device] = make_column_header1(Discretes)
# 		header2[device] = make_column_header2(Discretes)
# 		header = header1[device] + '\n' + header2[device] + '\n'
		
# 	outputs[number].write(header)
# 	header_length[device] = (len(header_len_re.findall(header)) / 2) + 1
# 	blank_data[device] = '\t' * header_length[device] + '\n'




for (device, number) in zip (list, number_list):
	print device, number
	file_name = device + '_data-' + time.strftime('%Y-%m-%d-%H%M') + '.txt'
	if output_dir != '':
		file_name = output_dir + '/' + file_name
	outputs[device] = open(file_name, 'w')
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
	else:
		header1[device] = make_column_header1(Discretes)
		header2[device] = make_column_header2(Discretes)
		header = header1[device] + '\n' + header2[device] + '\n'

	outputs[device].write(header)
	header_length[device] = (len(header_len_re.findall(header)) / 2) + 1
	blank_data[device] = '\t' * header_length[device] + '\n'








	
# set up output for merged data
file_name = 'All_data-' + time.strftime('%Y-%m-%d-%H%M') + '.txt'
outputs[4] = open(file_name, 'w')
header_row1 = 'Time'
header_row2 = '(sec)'
for device in list:
	header_row1 += '\t' + header1[device]
	header_row2 += '\t' + header2[device]
outputs[4].write(header_row1 + '\n' + header_row2 + '\n')

# set up queues
queues = {}
for device in list:
	queues[device] = Queue.Queue(0)
# print queues


# set up threads
class EFIS_thread(threading.Thread):
	def run(self):
		grab_efis_data(test_mode, data_rate, duration, serial_list, outputs, queues)

class EIS_thread(threading.Thread):
	def run(self):
		grab_eis_data(test_mode, data_rate, duration, serial_list, outputs, queues)

class GNS_thread(threading.Thread):
	def run(self):
		grab_gns_data(test_mode, data_rate, duration, serial_list, outputs, queues)
# 		grab_gns_data_new(test_mode, data_rate, duration, serial_list, outputs)

class Discretes_thread(threading.Thread):
	def run(self):
		grab_discrete_data(test_mode, data_rate, duration, serial_list, outputs, queues)

# start threads
Discretes_thread().start()
EFIS_thread().start()
EIS_thread().start()

# GPS outputs one record per second, so there is no need to try to use a higher data rate.
# if a higher data rate is selected, switch to one per second for the GPS.
if data_rate > 1:
	data_rate_temp = 1
	(data_rate, data_rate_temp) = (data_rate_temp, data_rate)
	GNS_thread().start()
	(data_rate, data_rate_temp) = (data_rate_temp, data_rate)
else:
	GNS_thread().start()

# print tell tale, to let us know it is still alive.
# count = 0
# while 1:
# 	time.sleep(1)
# 	print '*', count
# 	count += 1
# 	if os.path.exists('stop_recording.flag'):
# 		print 'Data recording stopping in 5 seconds, I hope.'
# 		time.sleep(5)
# 		break


# merge data streams from each device, using a queue for each device
# this will only work with live data, as the test data won't have synchronized
# time markers on the device data
sleep_time = 1.0 / data_rate
delay = 3
	
# for i in range(20):
# 	data = queues['D10A'].get()
# 	print 'EFIS data from queue is:', data
# 	time.sleep(sleep_time)
		
start_time = time.time()
raw_count = start_time * data_rate
count = int(raw_count)
data_time = start_time
counter = 0
data_count = data_time * data_rate

# time_re = re.compile(r'(^[0-9]10\.[0-9]+)\t')
while data_time < (start_time + duration * 60):
	data_time = time.time()
	if test_mode == '1':
		time.sleep(0.1)
	data_count = data_time * data_rate
	discretes_data_hold = ''
	if data_count >= count:
# 		# Pull data from all devices from their queues and assemble into a data line.
# 		# Poll all queues.  If the queue data is earlier than time, discard it.
# 		# If the queue data is too new (i.e. it has a time stamp that is later than this
# 		# block), put it in a temp variable to use it later.

		# the int() is needed to ensure the window_start is exactly at the even threshold
		# to avoid missing any data items that come in very close to the threshold.
		window_start = float(int(data_count - data_rate * delay)/data_rate)
		print 'Window start =:', window_start
		window_end = window_start + float(1 / data_rate)
		data_string = str(window_start)
		for device in list:
			data = pull_data_from_queue(window_start, window_end, device)
			data_string += '\t' + data
		print 'Data from queue is:', data_string
		outputs[4].write(data_string)
		outputs[4].write('\n')
		count += 1
		next_time = float(count / data_rate)
		time_to_sleep = max(next_time - time.time(), 0)
		print 'Time to sleep is:', time_to_sleep
		time.sleep(time_to_sleep)
#		print '*', counter
#		counter += 1
	


		# has the main thread sent a stop flag?
		if os.path.exists('stop_recording.flag'):
			print 'data merging stopping'
			break


# stop threads
# add code to allow the user to trigger a stop.  The code will create a file 'stop_recording.flag'.
# The threads check for this file after each data write, and terminate if this file is present.
# The script checks for this file at startup, and deletes it if present.

# stop = open('stop_recording.flag', 'w')

