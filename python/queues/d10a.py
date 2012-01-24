#! /sw/bin/python2.4

# TO DO 1. Rework data parsing using unpack('2s2s2s2s', data), etc
#          This will create a list of strings.  Use float() to convert
#          to numbers.  Run timing tests to compare to current approach.
#
#          Reworked to use unpack - almost exactly the same CPU time as
#          using slices.  About 12.8% on PMac at one record per second.
#          Stay with slices, as the code is a bit easier to read.
#
#       2. Completed, 4 Mar 06.
#
#       3. Fixed 21 Mar 06.  SVN version 279.

# DONE  2. Rework so test mode does not check for available serial ports.
#
#       3. Discern why the program hangs if the EFIS is shut down.  Testing
#          confirmed that the readline does not hang.  The one second timeout
#          works, and the code passes by it OK.
#
#          Fixed 21 Mar 06.  SVN version 279.

# NOTES
#
# 1. Data file growth rate is 948 KB per hour at 4 records per second.
#
# 2. Testing on 4 Mar 06 confirmed that the program can be started before the
#    EFIS is running, and that the EFIS can be shut down and restarted while
#    the program is running with no ill effect.  If there is no data coming
#    from the EFIS, then nothing is written to the file.
#
# 3. This module expects the EFIS to be on the second serial port.
#
# 4. Tested with EFIS SW version 02.11 on the Dynon D10A EFIS.
#
# 5. CPU useage is about 20% CPU on PBook at one record per second vs about 
#    13-14% for the perl script.  Tried using flush on the port, rather than
#    continually reading it, but this used almost 100% CPU time, and didn't 
#    actually flush the port.
#
# 6. Tested on aircraft on 7 Mar 06.
#
# 7. This version does not return the AOA, as it is not operative in my aircraft.


import time
import struct
import os.path
import Queue


class D10A:
	device_name = 'D10A'
	baudrate    =  115200
	bytesize    = 'EIGHTBITS'
	parity      = 'N'
	stopbits    =  1
	timeout     =  1
	xonxoff     =  0
	rtscts      =  0
	data_to_record   =  {'Hour': 1,
                       'Minute': 1,
                       'Second': 1,
                      'Counter': 1,
                        'Pitch': 1,
                         'Roll': 1,
                      'Heading': 1,
                           'IAS':1,
                     'Altitude': 1,
                    'Turn_Rate': 1,
                           'Ny': 1,
                           'Nz': 1,
                          'AOA': 0,
              'Status_Bit_Mask': 0,
                   'Product_ID': 0}
	order_label_units = [('Hour','Hr','Hr'),
                         ('Minute','Mn','Mn'),
                         ('Second','Sec','Sec'),
                         ('Counter','fractions of sec','.sec'),
                         ('Pitch','Pitch','deg'),
                         ('Roll','Bank','deg'),
                         ('Heading','Heading','deg mag'),
                         ('IAS','IAS','KIAS'),
                         ('Altitude','Baro Altitude','ft'),
                         ('Turn_Rate','Yaw rate','deg/s'),
                         ('Ny','Ny','g'),
                         ('Nz','Nz','g'),
                         ('AOA','AOA','??'),
                         ('Status_Bit_Mask','Status','??'),
                         ('Product_ID','Product ID','??')]
	scaling          =  {'Hour': 1,
                       'Minute': 1,
                       'Second': 1,
                      'Counter': 1,
                        'Pitch': 0.1,
                         'Roll': 0.1,
                      'Heading': 1,
# convert from tenths of meter/sec to knots
                           'IAS':0.1943846,
# convert from meters to feet
                     'Altitude': 3.28084,
                    'Turn_Rate': 1,
                           'Ny': 0.01,
                           'Nz': 0.1,
                          'AOA': 0.01,
              'Status_Bit_Mask': 1,
                   'Product_ID': 1}


def parse_efis(data_block):
	hour = data_block[0:2]
	minute = data_block[2:4]
	second = data_block[4:6]
	counter = data_block[6:8]

	pitch = data_block[8:12]
	pitch = str(float(pitch) / 10)

	roll = data_block[12:17]
	roll = str(float(roll) / 10)

	heading = data_block[17:20]

	ias = data_block[20:24]
	ias = str(float(ias) * 0.1943846)
	
	altitude = data_block[24:29]
	altitude = str(float(altitude) * 3.28084)

	turn_rate = data_block[29:33]

	ny = data_block[33:36]
	ny = str(float(ny) / 100)
	
	nz = data_block[36:39]
	nz = str(float(nz) / 10)
	
	aoa = data_block[39:41]
	status_bit_mask = data_block[41:47]
	product_id = data_block[47:51]
	check_sum = data_block[51:]
	
#	return [hour, minute, second, counter, pitch, roll, heading, ias, altitude, turn_rate, ny, nz, aoa, status_bit_mask, product_id, check_sum]

	return [hour, minute, second, counter, pitch, roll, heading, ias, altitude, turn_rate, ny, nz]

# def parse_efis_unpack(data_block):
# 	# this is more compact code, but uses a bit more CPU time than the version that uses list slices.
# 	fmt = '2s2s2s2s4s5s3s4s5s4s3s3s2s6s4s2s'
# 	(hour, minute, second, counter, pitch, roll, heading, ias, altitude, \
# 	  turn_rate, ny, nz, aoa, status_bit_mask, product_id, check_sum) = \
# 	  struct.unpack(fmt,data_block)
# 
# 	pitch = str(float(pitch) / 10)
# 	roll = str(float(roll) / 10)
# 	ias = str(float(ias) * 0.1943846)
# 	altitude = str(float(altitude) * 3.28084)
# 	ny = str(float(ny) / 100)
# 	nz = str(float(nz) / 10)
# 		
# # 	return [hour, minute, second, counter, pitch, roll, heading, ias, \
# # 	  altitude, turn_rate, ny, nz, aoa, status_bit_mask, product_id, \
# # 	  check_sum]
# 
# 	return [hour, minute, second, counter, pitch, roll, heading, ias, \
# 	  altitude, turn_rate, ny, nz]

 
def grab_efis_data(test_mode, data_rate, duration, serial_list, outputs, queues):
# def grab_efis_data(test_mode, data_rate, duration, serial_list, outputs, ):
	if test_mode == '1':
		data_source = file('/Users/kwh/ftdata/Tk/EFIS_raw_data.txt', 'rU')
		data_source_name = 'file'
	else:
		data_source = serial_list['D10A']
		data_source_name = 'serial port'

	print 'Starting EFIS thread.  Test mode =', test_mode, 'Data source is:', data_source
	
	start_time = time.time()
	raw_count = start_time * data_rate
	count = int(raw_count)
	data_time = start_time
	while data_time < (start_time + duration * 60):
		data_time = time.time()
# 		print data_time, 'Ready to readline from EFIS'
		data = data_source.readline()
# 		print data_time, 'Finished readline'
# 		print '=================================================='
		if test_mode == '1':
			data += '\n'
			time.sleep(0.1)
		data_count = data_time * data_rate
		if data_count >= count:
			if len(data) == 53:
				returned_data = parse_efis(data)
				data_string = '\t'.join(returned_data)
				data_string = str(data_time) + '\t' + data_string + '\n'
					
				outputs['D10A'].write(data_string)
				queues['D10A'].put(data_string)
				count = count + 1
				# print tell tale, to let us know it is still alive.
				print 'EFIS alive and recording.',
			else:
				print 'EFIS alive, but no data to record.',

		# has the main thread sent a stop flag?
		if os.path.exists('stop_recording.flag'):
			print 'EFIS data recording stopping'
			outputs['D10A'].close()
			return
	outputs['D10A'].close()

