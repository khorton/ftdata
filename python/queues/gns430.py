#! /sw/bin/python2.4

# did a one minute recording of raw data.  Got exactly 60 records.
# did another recording during startup ('/Users/kwh/ftdata/Tk/gns_1_mn_starting.dat').
# it shows how the various fields are filled during various stages of the GPS power up.

# TO DO 1. Add code to record flight plan waypoints, if present.
#
# DONE  2. Sort out why the script hangs, if the GNS is turned off first.
#          There is a one second timeout, so it shouldn't be blocking in a 
#          readline.
#
#          The script errors out when the USB cable is pulled from the laptop,
#          so this could be the shutdown routine.
#
#          Fixed 21 Mar 06.  SVN version 279.

import time
import re
import struct
import sys
import os.path
import Queue

block_size = 50

class GNS430:
	device_name = 'GNS430'
	baudrate    =  9600
	bytesize    = 'EIGHTBITS'
	parity      = 'N'
	stopbits    =  1
	timeout     =  1
	xonxoff     =  0
	rtscts      =  0
	data_to_record   =   {'ALT': 1,
                           'GS': 1,
                        'TRACK': 1,
                          'LAT': 1,
                         'LONG': 1,
                          'DTK': 1,
                          'XTK': 1,
                          'WPT': 1,
                     'WPT_DIST': 1,
                      'WPT_BRG': 1,
                      'MAG_VAR': 1,
                        'NAV_VALID': 0}
	order_label_units = [('GS','Grd Speed','kt'),
                         ('TRACK','Track','deg mag'),
                         ('ALT','GPS Altitude','ft'),
                         ('LAT','Latitude','deg N'),
                         ('LONG','Longitude','deg W'),
                         ('DTK','Desired Track','deg mag'),
                         ('XTK','Cross Track Error','nm R'),
                         ('WPT','Active Waypoint',''),
                         ('WPT_DIST','Distance to Waypoint','nm'),
                         ('WPT_BRG','Bearing to Waypoint','deg mag'),
                         ('MAG_VAR','Magnetic Variation','deg E'),
                         ('NAV_VALID','GPS Nav Status','')]
	scaling          =  {'TACH': 1,
                         'CHT1': 1,
                         'CHT2': 1,
                         'CHT3': 1,
                         'CHT4': 1,
                         'CHT5': 1,
                         'CHT6': 1,
                         'EGT1': 1,
                         'EGT2': 1,
                         'EGT3': 1,
                         'EGT4': 1,
                         'EGT5': 1,
                         'EGT6': 1,
                        'DAUX1': 1,
                        'DAUX2': 1,
                         'ASPD': 1,
                          'ALT': 1,
                         'VOLT': 0.1,
                    'FUEL_FLOW': 0.1,
                    'UNIT_TEMP': 1,
                         'CARB': 1,
                        'ROCSGN': 1,
                          'OAT': 1,
                         'OILT': 1,
                         'OILP': 1,
                         'AUX1': 0.1,
                         'AUX2': 1,
                         'AUX3': 1,
                         'AUX4': 1,
                         'COOL': 1,
                          'ETI': 0.1,
                          'QTY': 0.1,
                          'HRS': 1,
                          'MIN': 1,
                          'SEC': 1,
                       'ENDHRS': 1,
                       'ENDMIN': 1,
                         'BARO': 1,
                        'MAGHD': 1}
	gps_alt_re = re.compile('z(?P<GPS_alt>[0-9|-]{5})', re.DOTALL)
	gps_lat_re = re.compile('A(?P<GPS_lat_sign>[NS-])\s(?P<GPS_lat_deg>.{2})\s(?P<GPS_lat_min>.{4})', re.DOTALL)
	gps_long_re = re.compile('B(?P<GPS_long_sign>[EW-])\s(?P<GPS_long_deg>.{3})\s(?P<GPS_long_min>.{4})', re.DOTALL)
	gps_track_re = re.compile('C(?P<GPS_track>.{3})', re.DOTALL)
	gps_grd_speed_re = re.compile('D(?P<GPS_grd_speed>[0-9|-]{3})', re.DOTALL)
	gps_wpt_dist_re = re.compile('E(?P<GPS_dist_to_wpt>[0-9|-]{5})', re.DOTALL)
	gps_cross_track_re = re.compile('G(?P<GPS_cross_track_sign>[LR-])(?P<GPS_cross_track>.{4})', re.DOTALL)
	gps_desired_track_re = re.compile('I(?P<GPS_desired_track>[0-9|-]{4})', re.DOTALL)
	gps_wpt_re = re.compile('K(?P<GPS_wpt>.{5})', re.DOTALL)
	gps_wpt_brg_re = re.compile('L(?P<GPS_wpt_brg>[0-9|-]{4})', re.DOTALL)
	gps_mag_var_re = re.compile('Q(?P<GPS_mag_var_sign>[EW-])(?P<GPS_mag_var>.{3})', re.DOTALL)



#------------------------------------------------------------------------------#
#
# parse_gns_old(data_block)
#
# Parses GNS 430 data block and returns a list of individual data items.
#
# This is the original version, parsing a long data line using a series of
# regular expressions.
#------------------------------------------------------------------------------#
# def parse_gns_old(data_block):
# 	# look into using groups and re.findall or re.groupdict
# 	# altitude
# 	gps_alt_re = re.compile('z(?P<GPS_alt>[0-9|-]{5})', re.DOTALL)
# 	gps_alt_search = gps_alt_re.search(data_block)
# 	gps_alt = gps_alt_search.group('GPS_alt')
# #
# 	# latitude
# 	# sign convention - N latitude is positive, S latitude is negative
# 	gps_lat_re = re.compile('A(?P<GPS_lat_sign>[NS-])\s(?P<GPS_lat_deg>.{2})\s(?P<GPS_lat_min>.{4})', re.DOTALL)
# 	gps_lat_search = gps_lat_re.search(data_block)
# 	if gps_lat_search.group('GPS_lat_sign') != '-':
# 		gps_lat = float(gps_lat_search.group('GPS_lat_deg')) + \
# 		  float(gps_lat_search.group('GPS_lat_min')) / 6000
# 		if gps_lat_search.group('GPS_lat_sign') == 'S':
# 			gps_lat = gps_lat * -1
# 	else:
# 		gps_lat = ''
# #
# 	# longitude
# 	# sign convention - W longitude is positive, E longitude is negative
# 	gps_long_re = re.compile('B(?P<GPS_long_sign>[EW-])\s(?P<GPS_long_deg>.{3})\s(?P<GPS_long_min>.{4})', re.DOTALL)
# 	gps_long_search = gps_long_re.search(data_block)
# 	if gps_lat_search.group('GPS_lat_sign') != '-':
# 		gps_long = float(gps_long_search.group('GPS_long_deg')) + \
# 		  float(gps_long_search.group('GPS_long_min')) / 6000
# 		if gps_long_search.group('GPS_long_sign') == 'E':
# 			gps_long = gps_long * -1
# 	else:
# 		gps_long = ''
# 	
# 	# track
# 	gps_track_re = re.compile('C(?P<GPS_track>.{3})', re.DOTALL)
# 	gps_track_search = gps_track_re.search(data_block)
# 	gps_track = gps_track_search.group('GPS_track')
# 	if gps_track == '---':
# 		gps_track = ''
# 	
# 	# ground speed
# 	gps_grd_speed_re = re.compile('D(?P<GPS_grd_speed>[0-9|-]{3})', re.DOTALL)
# 	gps_grd_speed_search = gps_grd_speed_re.search(data_block)
# 	gps_grd_speed = gps_grd_speed_search.group('GPS_grd_speed')
# 	if gps_grd_speed == '---':
# 		gps_grd_speed = ''
# 	
# 	# distance to waypoint
# 	gps_wpt_dist_re = re.compile('E(?P<GPS_dist_to_wpt>[0-9|-]{5})', re.DOTALL)
# 	gps_wpt_dist_search = gps_wpt_dist_re.search(data_block)
# 	gps_wpt_dist = gps_wpt_dist_search.group('GPS_dist_to_wpt')
# 	if gps_wpt_dist == '-----':
# 		gps_wpt_dist = ''
# 	else:
# 		gps_wpt_dist = float(gps_wpt_dist) / 10
# 	
# 	# xtk
# 	# sign convention - R xtk is positive, L xtk is negative
# 	gps_cross_track_re = re.compile('G(?P<GPS_cross_track_sign>[LR-])(?P<GPS_cross_track>.{4})', re.DOTALL)
# 	gps_cross_track_search = gps_cross_track_re.search(data_block)
# 	gps_cross_track = gps_cross_track_search.group('GPS_cross_track')
# 	if gps_cross_track == '----':
# 		gps_cross_track = ''
# 	else:
# 		gps_cross_track = float(gps_cross_track) / 100.0
# 	if gps_cross_track_search.group('GPS_cross_track_sign') == 'L':
# 		gps_cross_track = gps_cross_track * -1
# 	
# 	# dtk
# 	gps_desired_track_re = re.compile('I(?P<GPS_desired_track>[0-9|-]{4})', re.DOTALL)
# 	gps_desired_track_search = gps_desired_track_re.search(data_block)
# 	gps_desired_track = gps_desired_track_search.group('GPS_desired_track')
# 	if gps_desired_track == '----':
# 		gps_desired_track = ''
# 	else:
# 		gps_desired_track = float(gps_desired_track) / 10.0
# 	
# 	# active waypoint
# 	gps_wpt_re = re.compile('K(?P<GPS_wpt>.{5})', re.DOTALL)
# 	gps_wpt_search = gps_wpt_re.search(data_block)
# 	gps_wpt = gps_wpt_search.group('GPS_wpt')
# 	if gps_wpt == '-----':
# 		gps_wpt = ''
# 	
# 	# brg to waypoint
# 	gps_wpt_brg_re = re.compile('L(?P<GPS_brg_to_wpt>[0-9|-]{4})', re.DOTALL)
# 	gps_wpt_brg_search = gps_wpt_brg_re.search(data_block)
# 	gps_wpt_brg = gps_wpt_brg_search.group('GPS_brg_to_wpt')
# 	if gps_wpt_brg == '----':
# 		gps_wpt_brg = ''
# 	else:
# 		gps_wpt_brg = float(gps_wpt_brg) / 10.0
# 	
# 	# mag var
# 	# sign convention - E mag var is positive, W xtk is negative
# 	gps_mag_var_re = re.compile('Q(?P<GPS_mag_var_sign>[EW-])(?P<GPS_mag_var>.{3})', re.DOTALL)
# 	gps_mag_var_search = gps_mag_var_re.search(data_block)
# 	gps_mag_var = gps_mag_var_search.group('GPS_mag_var')
# # 	print 'GPS mag var is:', gps_mag_var
# 	if gps_mag_var == '---':
# 		gps_mag_var = ''
# 	else:
# 		gps_mag_var = float(gps_mag_var) / 10.0
# 	if gps_mag_var_search.group('GPS_mag_var_sign') == 'W':
# 		gps_mag_var = gps_mag_var * -1
# 	
# 	# nav valid
# 	
# 	# 	
# 	return[gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, gps_wpt_dist, gps_cross_track, \
# 	gps_desired_track, gps_wpt, gps_wpt_brg, gps_mag_var]

#------------------------------------------------------------------------------#
#
# parse_gns(data_block)
#
# Parses GNS 430 data block and returns a list of individual data items.
#
# This is the second version, parsing a list of data items using a series of
# regular expressions.
#------------------------------------------------------------------------------#
def parse_gns(data_block_list):
	list_len = len(data_block_list)

	# gps altitude
	for n in range(list_len):
		gps_alt_search = GNS430.gps_alt_re.search(data_block_list[n])
		if gps_alt_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_alt = gps_alt_search.group('GPS_alt')
			break

	# latitude
	# sign convention - N latitude is positive, S latitude is negative
	for n in range(list_len):
		gps_lat_search = GNS430.gps_lat_re.search(data_block_list[n])
		if gps_lat_search:
			del data_block_list[n]
			list_len = list_len -1
			if gps_lat_search.group('GPS_lat_sign') != '-':
				gps_lat = float(gps_lat_search.group('GPS_lat_deg')) + \
				  float(gps_lat_search.group('GPS_lat_min')) / 6000
				if gps_lat_search.group('GPS_lat_sign') == 'S':
					gps_lat = gps_lat * -1
			else:
				gps_lat = ''
			break

	# longitude
	# sign convention - W longitude is positive, E longitude is negative
	for n in range(list_len):
		gps_long_search = GNS430.gps_long_re.search(data_block_list[n])
		if gps_long_search:
			del data_block_list[n]
			list_len = list_len -1
			if gps_lat_search.group('GPS_lat_sign') != '-':
				gps_long = float(gps_long_search.group('GPS_long_deg')) + \
				  float(gps_long_search.group('GPS_long_min')) / 6000
				if gps_long_search.group('GPS_long_sign') == 'E':
					gps_long = gps_long * -1
			else:
				gps_long = ''
			break

	# track
	for n in range(list_len):
		gps_track_search = GNS430.gps_track_re.search(data_block_list[n])
		if gps_track_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_track = gps_track_search.group('GPS_track')
			if gps_track == '---':
				gps_track = ''
			break

	# ground speed
	for n in range(list_len):
		gps_grd_speed_search = GNS430.gps_grd_speed_re.search(data_block_list[n])
		if gps_grd_speed_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_grd_speed = gps_grd_speed_search.group('GPS_grd_speed')
			if gps_grd_speed == '---':
				gps_grd_speed = ''
			break

	# distance to waypoint
	for n in range(list_len):
		gps_wpt_dist_search = GNS430.gps_wpt_dist_re.search(data_block_list[n])
		if gps_wpt_dist_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_wpt_dist = gps_wpt_dist_search.group('GPS_dist_to_wpt')
			if gps_wpt_dist == '-----':
				gps_wpt_dist = ''
			else:
				gps_wpt_dist = float(gps_wpt_dist) / 10
			break

	# xtk
	# sign convention - R xtk is positive, L xtk is negative
	for n in range(list_len):
		gps_cross_track_search = GNS430.gps_cross_track_re.search(data_block_list[n])
		if gps_cross_track_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_cross_track = gps_cross_track_search.group('GPS_cross_track')
			if gps_cross_track == '----':
				gps_cross_track = ''
			else:
				gps_cross_track = float(gps_cross_track) / 100.0
			if gps_cross_track_search.group('GPS_cross_track_sign') == 'L':
				gps_cross_track = gps_cross_track * -1
			break

	# dtk
	for n in range(list_len):
		gps_desired_track_search = GNS430.gps_desired_track_re.search(data_block_list[n])
		if gps_desired_track_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_desired_track = gps_desired_track_search.group('GPS_desired_track')
			if gps_desired_track == '----':
				gps_desired_track = ''
			else:
				gps_desired_track = float(gps_desired_track) / 10.0
			break

	# active waypoint
	for n in range(list_len):
		gps_wpt_search = GNS430.gps_wpt_re.search(data_block_list[n])
		if gps_wpt_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_wpt = gps_wpt_search.group('GPS_wpt')
			if gps_wpt == '-----':
				gps_wpt = ''
			break

	# brg to waypoint
	for n in range(list_len):
		gps_wpt_brg_search = GNS430.gps_wpt_brg_re.search(data_block_list[n])
		if gps_wpt_brg_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_wpt_brg = gps_wpt_brg_search.group('GPS_wpt_brg')
			if gps_wpt_brg == '----':
				gps_wpt_brg = ''
			else:
				gps_wpt_brg = float(gps_wpt_brg) / 10.0
			break

	# mag var
	# sign convention - E mag var is positive, W xtk is negative
	for n in range(list_len):
		gps_mag_var_search = GNS430.gps_mag_var_re.search(data_block_list[n])
		if gps_mag_var_search:
			del data_block_list[n]
			list_len = list_len -1
			gps_mag_var = gps_mag_var_search.group('GPS_mag_var')
			if gps_mag_var == '---':
				gps_mag_var = ''
			else:
				gps_mag_var = float(gps_mag_var) / 10.0
			if gps_mag_var_search.group('GPS_mag_var_sign') == 'W':
				gps_mag_var = gps_mag_var * -1
			break

# nav valid
# 	
# 
# 

	
	return[gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, gps_wpt_dist, gps_cross_track, \
	gps_desired_track, gps_wpt, gps_wpt_brg, gps_mag_var]

#	return[gps_alt, gps_lat, gps_long]


#------------------------------------------------------------------------------#
#
# grab_gns_data_old(test_mode, data_rate, duration, serial_list, outputs)
#
# Read GNS 430 data stream, assemble records, pass them to the parser at
# the required interval, then write the decoded record to disk.
#
# This is the original version, reading records by fixed size blocks.
#------------------------------------------------------------------------------#
# def grab_gns_data_old(test_mode, data_rate, duration, serial_list, outputs):
# 	if test_mode == '1':
# # 		data_source = file('/Users/kwh/ftdata/Tk/GNS430_raw_data_capture_20050310.dat', 'rU')
# 		data_source = file('/Users/kwh/ftdata/Tk/gns_1_mn_starting.dat', 'rU')
# 	else:
# 		data_source = serial_list[2]
# 
# 	print 'Starting GNS thread.  Test mode =', test_mode, 'Data source is:', data_source
# 
# 	match_start_of_block = re.compile('.*\x02(?P<re_first_part>.*)', re.DOTALL)
# 	match_whole_block = re.compile('.*\x02(?P<re_whole_record>.*)\x03(?P<re_first_part>.*)', re.DOTALL)
# 	
# 	start_time = time.time()
# 	raw_count = start_time * data_rate
# 	count = int(raw_count)
# 	data_time = start_time
# 	while data_time < (start_time + duration * 60):
# 		data_time = time.time()
# 		data = data_source.read(block_size)
# 		if test_mode == '1':
# #			print 'Sleeping'
# 			time.sleep(0.025)
# 		data_count = data_time * data_rate
# # 		print 'Starting, data_count =', data_count, '. Count =', count
# 		if data_count >= count:
# 			# Keeping reading data until the start of record marker is found
# 			match_start = ''
# 			while not match_start:
# 				if test_mode == '1':
# 					time.sleep(0.025)
# #					print 'Sleeping 2'
# 				data_in = data_source.read(block_size)
# 				if len(data_in) < block_size:
# 					print 'Ran out of data'
# # 					sys.exit(2)
# 				match_start = match_start_of_block.search(data_in)
# 				print 'In the start loop - no match.'
# 			
# 			data_block = match_start.group('re_first_part')
# 			
# 			# Read next part of data
# 			match_block = ''
# 			while not match_block:
# 				if test_mode == '1':
# 					time.sleep(0.2)
# #					print 'Sleeping 3'
# 				data_in = data_source.read(block_size)
# 				if len(data_in) < block_size:
# 					print 'Ran out of data'
# 					sys.exit(2)
# 				data_block = data_block + data_in
# 				match_block = match_whole_block.search(data_block)
# 				print 'In the whole block loop - no match.'
# 				if match_block:
# 					data = data_block + match_block.group('re_whole_record')
# 					next_data_start = match_block.group('re_first_part')
# # 				else:
# # 					data = data_test
# 					
# #			gns_decode = parse_gns(data_block)
# 			print 'GNS raw data block is:', data_block
# 			(gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, \
# 			gps_wpt_dist, gps_cross_track, gps_desired_track, \
# 			gps_wpt, gps_wpt_brg, gps_mag_var) = parse_gns(data_block)
# 				
# # 			print 'Returned data is:', gns_decode
# 			count = count + 1
# 				
# 				
# 			data_string = str(data_time) + '\t' + str(gps_grd_speed) + '\t'\
# 			+ str(gps_track) + '\t' + str(gps_alt) + '\t' + str(gps_lat) + '\t'\
# 			+ str(gps_long) + '\t' + str(gps_desired_track) + '\t' \
# 			+ str(gps_cross_track) + '\t' + str(gps_wpt) + '\t' \
# 			+ str(gps_wpt_dist) + '\t' + str(gps_wpt_brg) + '\t'\
# 			+ str(gps_mag_var) + '\n'
# 
# # 				+ str(oilt) + '\t' + str(oilp) + '\t' + str(volt) + '\t'\
# # 				+ str(eti) + '\t' + str(hrs) + '\t' + str(min) + '\t'\
# # 				+ str(sec) + '\t' + str(endhrs) + '\t' + str(endmin) + '\t' + str(unit) + '\n'
# 			outputs[2].write(data_string)
# 				
# # 			else:
# # 				print 'No GNS430 data match.'
 			
				

#------------------------------------------------------------------------------#
#
# grab_gns_data(test_mode, data_rate, duration, serial_list, outputs)
#
# Read GNS 430 data stream, assemble records, pass them to the parser at
# the required interval, then write the decoded record to disk.
#
# This version attempts use a trial improved algorithim, that reads by lines.
# It appears to be a bit more robust, but uses very slightly more CPU time.
#------------------------------------------------------------------------------#
def grab_gns_data(test_mode, data_rate, duration, serial_list, outputs, queues):
# def grab_gns_data(test_mode, data_rate, duration, serial_list, outputs, ):
	if test_mode == '1':
# 		data_source = file('/Users/kwh/ftdata/Tk/GNS430_raw_data_capture_20050310.dat', 'rU')
		data_source = file('/Users/kwh/ftdata/Tk/gns_1_mn_starting.dat', 'rU')
# 		data_source = file('/Users/kwh/ftdata/Tk/GNS_with_flt_plan.dat', 'rU')
	else:
		data_source = serial_list['GNS430']

	print 'Starting GNS thread.  Test mode =', test_mode, 'Data source is:', data_source

	match_start_of_block = re.compile('\x03\x02\x7a', re.DOTALL)
	
	start_time = time.time()
	raw_count = start_time * data_rate
	count = int(raw_count)
	data_time = start_time
	data = data_source.readline()
	while data_time < (start_time + duration * 60):
		data_time = time.time()
		if test_mode == '1':
#			print 'Sleeping'
			time.sleep(0.025)
		data_count = data_time * data_rate
# 		print 'Starting, data_count =', data_count, '. Count =', count
		if data_count >= count:
			# Keeping reading data until the start of record marker is found
			match_start = ''
			while not match_start:
				if test_mode == '1':
					time.sleep(0.025)
#					print 'Sleeping 2'
				match_start = match_start_of_block.search(data)
				if match_start:
# 					print 'Found start of record'
					break
# 				else:
# 					print '***No match***'
				data = data_source.readline()
			
			data_block_list = []
			data_block_list.append(data)
# 			print 'Start of data_block is:', data_block
			# we know there are at least 13 more lines in the data block
			for x in range(13):
				data = data_source.readline()
				data_block_list.append(data)
				if test_mode == '1':
					time.sleep(0.05)
#					print 'Sleeping 3'

			match_next = ''
			try_count = 0
			while not match_next:
				data = data_source.readline()
				match_next = match_start_of_block.search(data)
				if match_next:
					# this line is the first one for the next string
					# the data line read will be used as the first 
					# piece of the next data block
# 					print 'GNS data block is:', data_block_list
					break
				else:
					data_block_list.append(data)
					print 'GNS still looking for data block end. Tried', try_count, 'times.'
					try_count += 1
					if try_count > 20:
						break

			count = count + 1
			# print tell tale, to let us know it is still alive.
			print 'GNS has data ',

				
			(gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, \
			gps_wpt_dist, gps_cross_track, gps_desired_track, \
			gps_wpt, gps_wpt_brg, gps_mag_var) = parse_gns(data_block_list)

			data_string = str(data_time) + '\t' + str(gps_grd_speed) + '\t'\
			+ str(gps_track) + '\t' + str(gps_alt) + '\t' + str(gps_lat) + '\t'\
			+ str(gps_long) + '\t' + str(gps_desired_track) + '\t' \
			+ str(gps_cross_track) + '\t' + str(gps_wpt) + '\t' \
			+ str(gps_wpt_dist) + '\t' + str(gps_wpt_brg) + '\t'\
			+ str(gps_mag_var) + '\n'

# 			# this option doesn't work, as some fields are empty, and they are skipped.
# 			data_string_list = parse_gns2(data_block_list)
# 			for n in range(len(data_string_list)):
# 				data_string_list[n] = str(data_string_list[n])
# 			data_string = '\t'.join(data_string_list)
# 			data_string = str(data_time) + '\t' + data_string + '\n'

			outputs['GNS430'].write(data_string)
			queues['GNS430'].put(data_string)
			
			# has the main thread sent a stop flag?
			if os.path.exists('stop_recording.flag'):
				print 'GNS data recording stopping'
				outputs['GNS430'].close()
				return
	outputs['GNS430'].close()
				
#------------------------------------------------------------------------------#
#
# grab_gns_data_new(test_mode, data_rate, duration, serial_list, outputs)
#
# Read GNS 430 data stream, assemble records, pass them to the parser at
# the required interval, then write the decoded record to disk.
#
# This version attempts to redefine the end of line, to grab the whole block
# at once. This will only work if reading the serial port, as the readline
# method does not allow this.
#------------------------------------------------------------------------------#
# def grab_gns_data_new(test_mode, data_rate, duration, serial_list, outputs):
# 	if test_mode == '1':
# 		duration = 0
# 		print 'This function cannot be used with test data.'
# 		print 'GNS data recording stopping'
# 	else:
# 		data_source = serial_list[2]
# 		print 'Starting GNS thread.  Test mode =', test_mode, 'Data source is:', data_source
# 		data = data_source.readline(eol='\x03\x02\x7a')
# 		print 'Data:', data
# 
# 
# 	
# 	start_time = time()
# 	raw_count = start_time * data_rate
# 	count = int(raw_count)
# 	data_time = start_time
# 	while data_time < (start_time + duration * 60):
# 		data_time = time()
# 		data_count = data_time * data_rate
# 		if data_count >= count:
# 			# Keeping reading data until the start of record marker is found
# 			data = data_source.readline()
# 			print 'Data:', data

# 			data_block_list = []
# 			data_block_list.append(data)
# 			# we know there are at least 13 more lines in the data block
# 			for x in range(13):
# 				data = data_source.readline()
# 				data_block_list.append(data)
# 				if test_mode == '1':
# 					sleep(0.05)
# 
# 			match_next = ''
# 			while not match_next:
# 				data = data_source.readline()
# 				match_next = match_start_of_block.search(data)
# 				if match_next:
# 					# this line is the first one for the next string
# 					# the data line read will be used as the first 
# 					# piece of the next data block
# 					break
# 				else:
# 					data_block_list.append(data)

# 			count = count + 1
# 			# print tell tale, to let us know it is still alive.
# 			print 'GNS alive '

				
# 			(gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, \
# 			gps_wpt_dist, gps_cross_track, gps_desired_track, \
# 			gps_wpt, gps_wpt_brg, gps_mag_var) = parse_gns(data_block_list)
# 
# 			data_string = str(data_time) + '\t' + str(gps_grd_speed) + '\t'\
# 			+ str(gps_track) + '\t' + str(gps_alt) + '\t' + str(gps_lat) + '\t'\
# 			+ str(gps_long) + '\t' + str(gps_desired_track) + '\t' \
# 			+ str(gps_cross_track) + '\t' + str(gps_wpt) + '\t' \
# 			+ str(gps_wpt_dist) + '\t' + str(gps_wpt_brg) + '\t'\
# 			+ str(gps_mag_var) + '\n'
# 
# 
# 			outputs[2].write(data_string)
			
			# has the main thread sent a stop flag?
# 			if os.path.exists('stop_recording.flag'):
# 				print 'GNS data recording stopping'
# 				outputs['GNS430'].close()
# 				return
# 	outputs['GNS430'].close()

				
