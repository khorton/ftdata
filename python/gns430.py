#! /sw/bin/python2.4

# did a one minute recording of raw data.  Got exactly 60 records.
# did another recording during startup ('/Users/kwh/ftdata/Tk/gns_1_mn_starting.dat').
# it shows how the various fields are filled during various stages of the GPS power up.

# The Garmin 400 Series Installation Manual seems to imply that the serial output
# should contain all flight plan waypoints, however actual raw data recording
# shows that only the first eleven waypoints appear in the data stream.

# TO DO  1. Add code to record flight plan waypoints, if present.
#
#        2. Fixed.
#
#        3. Fixed.
#
#        4. Look at using Python Cookbook recipes 19.12 and maybe 19.20 to 
#           implement getting the whole record at once.

#
# DONE   2. Decode and return the Nav Valid field.
#
#        3. Sort out why the script hangs, if the GNS is turned off first.
#           There is a one second timeout, so it shouldn't be blocking in a 
#           readline.
#
#           The script errors out when the USB cable is pulled from the laptop,
#           so this could be the shutdown routine.
#
#           Fixed 21 Mar 06.  SVN version 279.

from __future__ import division
import time
import re
import struct
import sys
import os.path
# import Queue

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
                    'DEST_DIST': 1,
                    'NAV_VALID': 1,
                     'FLT_PLAN': 1}
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
                         ('DEST_DIST', 'Distance to Destination', 'nm'),
                         ('NAV_VALID','GPS Nav Status','1 = Valid'),
                         ('FLT_PLAN','GPS Waypoints','')]
    
    gps_alt_re = re.compile('z(?P<GPS_alt>[0-9|-]{5})', re.DOTALL)
    # following re is for parse_gns_new()
    gps_alt_re_new = re.compile('^(?P<GPS_alt>[0-9|-]{5})', re.DOTALL)
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
    gps_dest_dist_re = re.compile('l(?P<GPS_dist_dist>[0-9]{6})', re.DOTALL)
    gps_nav_valid_re = re.compile('S(?P<GPS_nav_valid>-----)', re.DOTALL)
#   gps_waypoint_re = re.compile('w(?P<wpt_num>[0-9]{2}).(?P<wpt>[\w|\s]{5}).*', re.DOTALL)
#   gps_waypoint_re = re.compile('w[0-9]{2}.(?P<wpt>[\w|\s]{5}).*', re.DOTALL)
    gps_waypoint_re = re.compile('w[0-9]{2}.([\w|\s]{5})', re.DOTALL)
#   # there is an embedded newline character in the waypoint line for the 10th waypoint.
#   gps_waypoint10_re = re.compile('(?P<wpt>[\w|\s]{5}).*', re.DOTALL)



#------------------------------------------------------------------------------#
#
# parse_gns_old(data_block)
#
# Parses GNS 430 data block and returns a list of individual data items.
#
#------------------------------------------------------------------------------#
def parse_gns_old(data_block_list):
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
    for n in range(list_len):
        gps_nav_valid_search = GNS430.gps_nav_valid_re.search(data_block_list[n])
        if gps_nav_valid_search:
            del data_block_list[n]
            list_len = list_len -1
            nav_valid = '1'
        else:
            nav_valid = '0'
        break
        
    
    return[gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, gps_wpt_dist, gps_cross_track, \
    gps_desired_track, gps_wpt, gps_wpt_brg, gps_mag_var, nav_valid]

#------------------------------------------------------------------------------#
#
# parse_gns(data_block)
#
# Parses GNS 430 data block and returns a list of individual data items.
# This version expects to receive the whole block as one chunk.
#
#------------------------------------------------------------------------------#
def parse_gns(data_block):
    
    # gps altitude
    gps_alt_search = GNS430.gps_alt_re_new.search(data_block)
    if gps_alt_search:
        gps_alt = gps_alt_search.group('GPS_alt')
    else:
        gps_alt = ''
        
    # latitude
    # sign convention - N latitude is positive, S latitude is negative
    gps_lat_search = GNS430.gps_lat_re.search(data_block)
    if gps_lat_search:
        try:
            gps_lat = float(gps_lat_search.group('GPS_lat_deg')) + \
              float(gps_lat_search.group('GPS_lat_min')) / 6000
        except ValueError:
            gps_lat = ''
        if gps_lat_search.group('GPS_lat_sign') == 'S':
            gps_lat = gps_lat * -1
    else:
        gps_lat = ''
        
    # longitude
    # sign convention - W longitude is positive, E longitude is negative
    gps_long_search = GNS430.gps_long_re.search(data_block)
    if gps_long_search:
        try:
            gps_long = float(gps_long_search.group('GPS_long_deg')) + \
              float(gps_long_search.group('GPS_long_min')) / 6000
        except ValueError:
            gps_long = ''
        if gps_long_search.group('GPS_long_sign') == 'E':
            gps_long = gps_long * -1
    else:
        gps_long = ''
        
    # track
    gps_track_search = GNS430.gps_track_re.search(data_block)
    if gps_track_search:
        gps_track = gps_track_search.group('GPS_track')
        if gps_track == '---':
            gps_track = ''
    else:
        gps_track = ''
    
    # ground speed
    gps_grd_speed_search = GNS430.gps_grd_speed_re.search(data_block)
    if gps_grd_speed_search:
        gps_grd_speed = gps_grd_speed_search.group('GPS_grd_speed')
        if gps_grd_speed == '---':
            gps_grd_speed = ''
    else:
        gps_grd_speed = ''
        
    # distance to waypoint
    gps_wpt_dist_search = GNS430.gps_wpt_dist_re.search(data_block)
    if gps_wpt_dist_search:
        gps_wpt_dist = gps_wpt_dist_search.group('GPS_dist_to_wpt')
        if gps_wpt_dist == '-----':
            gps_wpt_dist = ''
        else:
            gps_wpt_dist = float(gps_wpt_dist) / 10
    else:
        gps_wpt_dist = ''
        
    # xtk
    # sign convention - R xtk is positive, L xtk is negative
    gps_cross_track_search = GNS430.gps_cross_track_re.search(data_block)
    if gps_cross_track_search:
        gps_cross_track = gps_cross_track_search.group('GPS_cross_track')
        if gps_cross_track == '----':
            gps_cross_track = ''
        else:
            gps_cross_track = float(gps_cross_track) / 100.0
        if gps_cross_track_search.group('GPS_cross_track_sign') == 'L':
            gps_cross_track = gps_cross_track * -1
    else:
        gps_cross_track = ''
        
    # dtk
    gps_desired_track_search = GNS430.gps_desired_track_re.search(data_block)
    if gps_desired_track_search:
        gps_desired_track = gps_desired_track_search.group('GPS_desired_track')
        if gps_desired_track == '----':
            gps_desired_track = ''
        else:
            gps_desired_track = float(gps_desired_track) / 10.0
    else:
        gps_desired_track = ''
        
    # active waypoint
    gps_wpt_search = GNS430.gps_wpt_re.search(data_block)
    if gps_wpt_search:
        gps_wpt = gps_wpt_search.group('GPS_wpt')
        if gps_wpt == '-----':
            gps_wpt = ''
    else:
        gps_wpt = ''
    
    # brg to waypoint
    gps_wpt_brg_search = GNS430.gps_wpt_brg_re.search(data_block)
    if gps_wpt_brg_search:
        gps_wpt_brg = gps_wpt_brg_search.group('GPS_wpt_brg')
        if gps_wpt_brg == '----':
            gps_wpt_brg = ''
        else:
            gps_wpt_brg = float(gps_wpt_brg) / 10.0
    else:
        gps_wpt_brg = ''
        
    # mag var
    # sign convention - E mag var is positive, W xtk is negative
    gps_mag_var_search = GNS430.gps_mag_var_re.search(data_block)
    if gps_mag_var_search:
        gps_mag_var = gps_mag_var_search.group('GPS_mag_var')
        if gps_mag_var == '---':
            gps_mag_var = ''
        else:
            gps_mag_var = float(gps_mag_var) / 10.0
        if gps_mag_var_search.group('GPS_mag_var_sign') == 'W':
            gps_mag_var = gps_mag_var * -1
    else:
        gps_mag_var = ''
        
    # dest dist
    gps_dest_dist_search = GNS430.gps_dest_dist_re.search(data_block)
    if gps_dest_dist_search:
        dest_dist = float(gps_dest_dist_search.group('GPS_dist_dist')) / 10
    else:
        dest_dist = ''
        
    # nav valid
    gps_nav_valid_search = GNS430.gps_nav_valid_re.search(data_block)
    if gps_nav_valid_search:
        nav_valid = '1'
    else:
        nav_valid = '0'
    
    # waypoint list
    gps_waypoints_list = GNS430.gps_waypoint_re.findall(data_block)
    if gps_waypoints_list:
        for index, item in enumerate(gps_waypoints_list):
            gps_waypoints_list[index] = item.rstrip()
        gps_waypoints = ', '.join(gps_waypoints_list)
        print 'Waypoint list is:', gps_waypoints
    else:
        gps_waypoints = ''
        print 'There are no GPS waypoints.'
        
    return[gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, gps_wpt_dist,\
      gps_cross_track, gps_desired_track, gps_wpt, gps_wpt_brg, gps_mag_var,\
      dest_dist, nav_valid, gps_waypoints]

#------------------------------------------------------------------------------#
#
# grab_gns_data_old(test_mode, data_rate, duration, serial_list, outputs)
#
# Read GNS 430 data stream, assemble records, pass them to the parser at
# the required interval, then write the decoded record to disk.
#
# This version attempts use a trial improved algorithim, that reads by lines.
# It appears to be a bit more robust, but uses very slightly more CPU time.
#------------------------------------------------------------------------------#
def grab_gns_data_old(test_mode, data_rate, duration, serial_list, outputs, ):
    if test_mode == '1':
#       data_source = file('/Users/kwh/ftdata/Tk/GNS430_raw_data_capture_20050310.dat', 'rU')
#       data_source = file('/Users/kwh/ftdata/Tk/gns_1_mn_starting.dat', 'rU')
        data_source = file('/Users/kwh/ftdata/Tk/gns_1_mn.dat', 'rU')
#       data_source = file('/Users/kwh/ftdata/Tk/GNS_with_flt_plan.dat', 'rU')
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
#           print 'Sleeping'
            time.sleep(0.025)
        data_count = data_time * data_rate
#       print 'Starting, data_count =', data_count, '. Count =', count
        if data_count >= count:
            # Keeping reading data until the start of record marker is found
            match_start = ''
            while not match_start:
                if test_mode == '1':
                    time.sleep(0.025)
#                   print 'Sleeping 2'
                match_start = match_start_of_block.search(data)
                if match_start:
#                   print 'Found start of record'
                    break
#               else:
#                   print '***No match***'
                data = data_source.readline()
            
            data_block_list = []
#           waypoint_list = []
#           waypoint10_next_flag = False
            data_block_list.append(data)
#           print 'Start of data_block is:', data_block
            # we know there are at least 13 more lines in the data block
            for x in range(13):
                data = data_source.readline()
                data_block_list.append(data)
                if test_mode == '1':
                    time.sleep(0.05)
#                   print 'Sleeping 3'
    
            match_next = ''
            try_count = 0
            while not match_next:
                data = data_source.readline()
                match_next = match_start_of_block.search(data)
                if match_next:
                    # this line is the first one for the next string
                    # the data line read will be used as the first 
                    # piece of the next data block
#                   print 'GNS data block is:', data_block_list
                    break
                else:
#                   if waypoint10_next_flag == True:
#                       print 'In the waypoint 10 loop'
#                       # the 10th waypoint is not a complete line, as the third character is a newline
#                       data = data_source.readline()
#                       waypoint_line = GNS430.gps_waypoint10_re.search(data)
#                       if waypoint_line:
#                           waypoint = waypoint_line.group('wpt')
#                           print 'Waypoint 10 is:', waypoint
#                       waypoint10_next_flag = False
#                   else:
#                       waypoint_line = GNS430.gps_waypoint_re.match(data)
#                       if waypoint_line:
#                           waypoint = waypoint_line.group('wpt')
#                           print 'Waypoint is:', waypoint
#                           waypoint9 = waypoint_line.group('wpt9')
#                           if waypoint9 == '09':
#                               waypoint10_next_flag = True
#                               print 'Setting waypoint 10 flag.'
                    data_block_list.append(data)
                    print 'GNS still looking for data block end. Tried', try_count, 'times.'
                    try_count += 1
                    if try_count > 20:
                        break
                        
            # print tell tale, to let us know it is still alive.
            print 'GNS has data ',
                
            (gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, \
            gps_wpt_dist, gps_cross_track, gps_desired_track, \
            gps_wpt, gps_wpt_brg, gps_mag_var, nav_valid, gps_waypoints) = parse_gns(data_block_list)
            
            data_string = str(data_time) + '\t' + str(gps_grd_speed) + '\t'\
            + str(gps_track) + '\t' + str(gps_alt) + '\t' + str(gps_lat) + '\t'\
            + str(gps_long) + '\t' + str(gps_desired_track) + '\t' \
            + str(gps_cross_track) + '\t' + str(gps_wpt) + '\t' \
            + str(gps_wpt_dist) + '\t' + str(gps_wpt_brg) + '\t'\
            + str(gps_mag_var) + '\t' + nav_valid + '\t' + gps_waypoints +'\n'
            
#           # this option doesn't work, as some fields are empty, and they are skipped.
#           data_string_list = parse_gns2(data_block_list)
#           for n in range(len(data_string_list)):
#               data_string_list[n] = str(data_string_list[n])
#           data_string = '\t'.join(data_string_list)
#           data_string = str(data_time) + '\t' + data_string + '\n'
    
            outputs['GNS430'].write(data_string)
#           queues['GNS430'].put(data_string)
            count = count + 1
            
            # has the main thread sent a stop flag?
            if os.path.exists('stop_recording.flag'):
                print 'GNS data recording stopping'
                outputs['GNS430'].close()
                return
    print 'GNS 430 data recording shutting down'
    outputs['GNS430'].close()

#------------------------------------------------------------------------------#
#
# grab_gns_data(test_mode, data_rate, duration, serial_list, outputs)
#
# Reads GNS 430 data stream, assembles records, pass them to the parser at
# the required interval, then write the decoded record to disk.
#
#------------------------------------------------------------------------------#
def grab_gns_data(test_mode, data_rate, duration, serial_list, outputs, ):
    block_size = 50
    tail = data_chunk = ''
    eor='\x03\x02\x7a'
    if test_mode == '1':
#       data_source = file('/Users/kwh/ftdata/Tk/GNS430_raw_data_capture_20050310.dat', 'rU')
#       data_source = file('/Users/kwh/ftdata/Tk/gns_1_mn_starting.dat', 'rU')
#       data_source = file('/Users/kwh/ftdata/Tk/gns_1_mn.dat', 'rU')
        data_source = file('/Users/kwh/ftdata/Tk/GNS_with_flt_plan.dat', 'rU')
    else:
        data_source = serial_list['GNS430']
        
    print 'Starting GNS thread.  Test mode =', test_mode, 'Data source is:', data_source
    
    start_time = time.time()
    raw_count = start_time * data_rate
    count = int(raw_count)
    data_time = start_time
    while data_time < (start_time + duration * 60):
        data_time = time.time()
        if test_mode == '1':
#           print 'Sleeping'
            time.sleep(1)
        data_count = data_time * data_rate
#       print 'Starting, data_count =', data_count, '. Count =', count
        while data_count < count:
            # read data to keep up with the input while waiting for time to actually record
            data_chunk = data_source.read(block_size)
            
        # assemble the next record to arrive
        running_data = tail + data_chunk
        pieces = running_data.split(eor)
        
        while len(pieces) < 2:
            # the second piece will appear once we hit the end of record marker
            data_chunk = data_source.read(block_size)
            running_data += data_chunk
            pieces = running_data.split(eor)
        
        # we hit the start of the record, so the second piece is the one we want
        # grab the time, so we know the approximate data time
        data_time = time.time()
        
        while len(pieces) < 3:
            # the third piece will appear once we hit the next end of record marker
            data_chunk = data_source.read(block_size)
            running_data += data_chunk
            pieces = running_data.split(eor)
        
        # we now have a complete data record
        tail = pieces[2]
        data_record = pieces[1]
        
        print 'Sending GNS data to parser.'
        
        [gps_alt, gps_lat, gps_long, gps_track, gps_grd_speed, gps_wpt_dist, \
          gps_cross_track, gps_desired_track, gps_wpt, gps_wpt_brg,
          gps_mag_var, dest_dist, nav_valid, gps_waypoints] = parse_gns(data_record)
          
        data_string = str(data_time) + '\t' + str(gps_grd_speed) + '\t'\
        + str(gps_track) + '\t' + str(gps_alt) + '\t' + str(gps_lat) + '\t'\
        + str(gps_long) + '\t' + str(gps_desired_track) + '\t' \
        + str(gps_cross_track) + '\t' + str(gps_wpt) + '\t' \
        + str(gps_wpt_dist) + '\t' + str(gps_wpt_brg) + '\t'\
        + str(gps_mag_var) + '\t' + str(dest_dist) + '\t'+ nav_valid + '\t' + gps_waypoints +'\n'
        
        outputs['GNS430'].write(data_string)
        
#       data = parse_gns(data_record)
#       data_string = '\t'.join(str(data))
    
#       outputs['GNS430'].write(str(data_time))
#       outputs['GNS430'].write('\t')
#       outputs['GNS430'].write(data_string)
#       outputs['GNS430'].write('\n')
    
#       outputs['GNS430'].write(str(data_time) + '\t' + data_string + '\n')
    
        count = count + 1
        
        # has the main thread sent a stop flag?
        if os.path.exists('stop_recording.flag'):
            print 'GNS data recording stopping'
            outputs['GNS430'].close()
            return
            # break
    print 'GNS 430 data recording shutting down'
    outputs['GNS430'].close()

#------------------------------------------------------------------------------#
#
# grab_gns_data_test(test_mode, data_rate, duration, serial_list, outputs)
#
# Attempt to read GNS 430 data stream, redefining the end of line to match the 
# data format.  It doesn't work.
#
#------------------------------------------------------------------------------#
def grab_gns_data_test(test_mode, data_rate, duration, serial_list, outputs, ):
    
    data_source = serial_list['GNS430']
    
    print 'Starting test GNS thread.  Test mode =', test_mode, 'Data source is:', data_source
    
    while 1:
        print 'in the loop'
        data_block = data_source.readline(eol='\x03\x02\x7a')
#       data_block = data_source.readline(eol='\x02\x7a')
        print 'GNS' 
        print data_block

        if os.path.exists('stop_recording.flag'):
            print 'GNS data recording stopping'
            outputs['GNS430'].close()
            return
