#! /usr/bin/env python

"""
merge_ftdata.py

script to merge data files from Grand Rapids EIS 4000 engine monitor, 
Dynon D-10A EFIS, Garmin GNS-430 GPS and a discrete event marker into 
a single file. 
"""
# TO DO:  1. Add code to handle potential phase delays between the various
#            devices.

#------------------------------------------------------------------------------#
#
# get_options()
#
# Define and parse command line options
#
#------------------------------------------------------------------------------#
from __future__ import division

def get_options():
    """
    Define and parse command line options
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.usage = "%prog [options] file_name\nor\n %prog -h"
    parser.add_option("-r", "--rate", dest="data_rate", default="0",
       help="Data rate in records per second. Defaults to the same data rate as \
the original data.", 
       metavar="data_rate")
    parser.add_option("-i", "--input", dest="input", 
       help="Define one of the input files.", metavar="input files")
    parser.add_option("-o", "--output", dest="output_dir", default="", 
       help="Define output directory.  Default is the script directory", 
       metavar="output directory")
    parser.add_option("-g", "--no_gns", action="store_false", 
       dest="gns_430_avail", default=True, help="No GNS 430 data to merge.")
    
    (options, args) = parser.parse_args()
    
    if args:
        file_name = args[0]
    elif options.input:
        file_name = options.input
    else:
        parser.error('Error - You must supply one of the input file names.\nThe\
 file name can either be bare after the script name, or it can be \
given following an "-i".  ')
    data_rate = float(options.data_rate)
    return file_name, data_rate, options.output_dir, options.gns_430_avail

#------------------------------------------------------------------------------#
#
# get_file_names(file_name)
#
# Given the name of one input file, get the other names.
#
#------------------------------------------------------------------------------#

def get_file_names(file_name):
    """
    Given the name of one input file, get the other names
    """
    file_data = re.search('_data-([0-9]{4})-([0-9]{2})-([0-9]{2})-([0-9]{2})\
([0-9]{2})\.txt',file_name)
    try:
        (year, month, day, hour, minute) = file_data.groups()
    except:
        print 'The file name is not in the expected format.  It must look like \
device_data_yyyy_mm_dd_time.txt'
        return
        
    file_names = []
    for item in device_list:
        file_names.append(item + '_data-' + str(year) + '-' + str(month) + '-' \
          + str(day) + '-' + str(hour) + str(minute) + '.txt')
    return file_names, year, month, day, hour, minute

#------------------------------------------------------------------------------#
#
# get_header(files)
#
# Read data files and pull out the column headers
#
# Also count the number of columns for each device, and create the blank line to
# be used if no device data is present at a given time.
#
#------------------------------------------------------------------------------#
def get_header(files):
    """
    Read data files and pull out the column headers
    
    Also count the number of columns for each device, and create the blank line
    to be used if no device data is present at a given time
    """
    tab_split_re = re.compile(r'\t')
    
    header_length = {}
    blank_data = []
    
    # Create first two lines, plus the first item in the third line
    header = 'RV-8 C-GNHK Flight Test Data from ' + date + \
      '\n\nTime\tElapsed Time\tUnix Time\t'
      
    # Remove the class name and the period from the time item
    trim_class = re.compile(r'^.+\.(?P<device_name>.+)$')
    
    # get third line in the header
    for file, device in zip(files, device_list):
        file.readline()
        file.readline()
        temp = file.readline()
        match = trim_class.search(temp)
        match_group = match.group('device_name')
        header += match_group + '\t'
        
        # measure the number of data colums so a proper length blank data line
        # can be put in the data for times when no device data is present.
        header_length[device] = len(tab_split_re.findall(match_group)) + 1
        blank_data.append('\t' * header_length[device])
        # Add GNS 430 header info manually, if the file is not valid
    if gns_430_avail == False:
        header += "GNS430 Time	Grd Speed	Track	GPS Altitude	Latitude	Longitude	Desired Track	Cross Track Error	Active Waypoint	Distance to Waypoint	Bearing to Waypoint	Magnetic Variation	Distance to Destination	GPS Nav Status	GPS Waypoints"
    header = header[:-1] + '\n'
    
    # get fourth line in the header
    header += '(H:M:S)\t(seconds)\t(seconds)\t'
    for file in files:
        header += file.readline()[:-1] + '\t'
        # Add GNS 430 header info manually, if the file is not valid
    if gns_430_avail == False:
        header += "(seconds)	(kt)	(deg mag)	(ft)	(deg N)	(deg W)	(deg mag)	(nm R)	()	(nm)	(deg mag)	(deg E)	(nm)	(1 = Valid)	()"
    header = header[:-1] + '\n'
    return header, blank_data


#------------------------------------------------------------------------------#
#
# get_start_time(files)
#
# Reads the data files and extracts the time of the first data record in any
# file
#
#------------------------------------------------------------------------------#
def get_start_time(files):
    """
    Reads the data files and extracts the time of the first data record in any
    file
    """
    line_items = []
    for n, file in enumerate(files):
        line_cache.append(file.readline())
        line_items.append(re.split('\t',line_cache[n]))
        line_cache_flag[n] = True
    
    start_time = float(line_items[0][0])
    for line_item in line_items:
        try:
            line_item[0] = float(line_item[0])
            if line_item[0] < start_time:
                start_time = line_item[0]
            line_cache_time.append(line_item[0])
        except:
            print "ERROR on %s" % line_item[0]
            pass
    print "start time = %s" % start_time
    return start_time


#------------------------------------------------------------------------------#
#
# get_file_id(device)
#
# Determine which file has the data for the given device
#
#------------------------------------------------------------------------------#
def get_file_id(device):
    """
    Determine which file has the data for the given device
    """
    for index, item in enumerate(device_list):
        if item == device:
            print 'Discretes is item', index
            return index

#------------------------------------------------------------------------------#
#
# get_data_rate(file)
#
# Read the file to determine its data rate.
#
#------------------------------------------------------------------------------#
def get_data_rate(file):
    """
    Read the file to determine its data rate
    """
    all_file_data = file.readlines()
    # reset the file pointer to the start of the file
    file.seek(0)
    file_len = len(all_file_data)
    line_time_10 = float(re.split('\t', all_file_data[9])[0])
    line_time_end = float(re.split('\t', all_file_data[-1])[0])
    file_data_rate = (file_len - 10) / (line_time_end - line_time_10)
    return round(file_data_rate, 2)


#------------------------------------------------------------------------------#
#
# make_temp_discretes(discretes_file, new_file)
#
# Create a temporary discretes file.  This temp file will be at the selected
# data rate, and will have the discretes markers set if they were set at any
# of the time slices between times at the selected data rate.
#
#------------------------------------------------------------------------------#
def make_temp_discretes(discretes_file, start_time, data_rate):
    """
    Create a temporary discretes file.  This temp file will be at the selected 
    data rate, and will have the discretes markers set if they were set at any
    of the time slices between times at the selected data rate
    """
#   temp_discretes_file_name = 'Temp_' + discretes_file.name
#   temp_discretes = file(temp_discretes_file_name, 'w')
    temp_discretes = tempfile.TemporaryFile()
    time_in_line = re.compile('^(?P<time>[0-9]+\.[0-9]+)\t(?P<discrete>.+)')
    
    # read file into memory
    temp_data = discretes_file.readlines()
    
    # reverse the list of lines, so list.pop() will get the first line
    temp_data.reverse()
    discrete_cache = 0
    count = 0
    time = 0
    # print temp_data
    while 1:
        window_start = start_time + count / data_rate
        window_end = window_start + 1 / data_rate
        try:
            line = temp_data.pop()
        except:
            print "Error when popping temp_data.  Window start=%s, and window end=%s" % (window_start, window_end)
            print "This may be normal.  Check the merged data file for validity."
        while time < window_end:
            try:
                line = temp_data.pop()
            except IndexError:
                # we are at the end of the data, so cleanup and return the new
                # discretes file
#               temp_discretes.close()
#               temp_discretes = file(temp_discretes_file_name, 'r')
                temp_discretes.seek(0)
                return temp_discretes
                
            match = time_in_line.match(line)
            try:
                temp_time, discrete = match.group('time', 'discrete')
                temp_time = float(temp_time)
                discrete = int(discrete)
            except AttributeError:
                count -= 1
                break
            if temp_time >= window_end:
                output_string = str(window_start) + '\t' + str(discrete_cache) + '\n'
                temp_discretes.write(output_string)
                discrete_cache = discrete
                break
            else:
                discrete_cache = max(discrete, discrete_cache)
                time = temp_time
        count += 1



#------------------------------------------------------------------------------#
#
# process_time_slice(window_start, window_end, offset)
#
# Read the next line from each file, and see if it falls in the correct time 
# slice.  If so, use it in the output.  If not, use blank data for the output
# and save the data for the next time.
#
#------------------------------------------------------------------------------#
def process_time_slice(window_start, window_end, offset):
    """
    Read the next line from each file, and see if it falls in the correct time 
    slice.  If so, use it in the output.  If not, use blank data for the output
    and save the data for the next time.
    """
#   line_out = str(window_start) + '\t'
#   line_out = time.ctime(window_start) + str(window_start) + '\t'
    if data_rate <= 1:
        line_out = time.strftime('%H:%M:%S',time.localtime(window_start)) +\
          '\t' + str(window_start - offset) + '\t' + str(window_start) + '\t'
    else:
        # append the second fraction to the second value, as there is more than
        # record per second.
        frac_sec = '%.2f'%(window_start % 1)
        frac_sec = frac_sec[1:]
        line_out = time.strftime('%H:%M:%S',time.localtime(window_start)) +\
          frac_sec + '\t' + str(window_start - offset) + '\t' + str(window_start) + '\t'
          
    for n, line in enumerate(line_cache):
        if line_cache_flag[n] == True:
            try:
                line_out = check_if_line_time_late(n, line_cache_time[n],\
                window_end, line_cache[n], line_out)
            except:
                pass
        else:
            # case - line_cache_flag == False
            line_time = float(0)
            while line_time < window_start:
                new_line = files[n].readline()
                try:
                    line_time = float(re.split('\t', new_line)[0])
                except ValueError:
                    print 'At the end of the data.  Shutting down.'
                    line_out = None
                    return line_out
            line_out = check_if_line_time_late(n, line_time, window_end,\
              new_line, line_out)
    # Add GNS 430 blank data manually, if the file is not valid
    if gns_430_avail == False:
        line_out += gns_blank_line
    line_out += '\n'
    return line_out

#------------------------------------------------------------------------------#
#
# check_if_line_time_late(line_time, window_end, line, line_out):
#
# Determine if the line time is too late for the current time slice.
# If the time is OK, use the line, kill the cache flag, and return the data.
#
# If the time is too late, call the cache_the_line function to cache the line, 
# then return the data.
#
#------------------------------------------------------------------------------#
def check_if_line_time_late(n, line_time, window_end, line, line_out):
    """
    Determine if the line time is too late for the current time slice. 
    If the time is OK, use the line, kill the cache flag, and return the data.
    
    If the time is too late, call the cache_the_line function to cache the 
    line, then return the data.
    """
    if float(line_time) < float(window_end):
        # remove last character, if if is a line feed (\n)
        if line[-1] == '\n':
            line_out += line[:-1] + '\t'
        else:
            line_out += line + '\t'
            print 'In the non-line-feed part.  Why am I here?\
              Something is wrong.'
        line_cache_flag[n] = False
        return line_out
    else:
        line_out = cache_the_line(n, line_time, line, line_out)
        return line_out

    
#------------------------------------------------------------------------------#
#
# cache_the_line(line_time, window_end, line):
#
# The line time is too late, so it cannot be used.  But it will be needed
# later, so cache it, set the cache flag, and return blank data.
#
#------------------------------------------------------------------------------#
def cache_the_line(n, line_time, line, line_out):
    """
    The line time is too late, so it cannot be used.  But it will be needed
    later, so cache it, set the cache flag, and return blank data.
    """
    line_cache[n] = line
    line_cache_time[n] = line_time
    line_cache_flag[n] = True
    line_out += blank_data[n]
    return line_out

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#
#
# Main code starts here.  Everything above is just function definitions.
#
#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

import re
import time
import tempfile

print 'Doing the initial setup work.  This phase takes a few seconds.'
# This list defines the order that the device data will show up in the
# merged file, from left to right.

# read command line options
file_name, data_rate, output_dir, gns_430_avail = get_options()

device_list = [ 'Discretes', 'D10A', 'EIS4000', 'GNS430']
number_of_header_lines = 4

# if GNS 430 data is not available, remove it from the device list
if gns_430_avail == False:
    device_list.remove('GNS430')
    gns_blank_line = 15 * '\t'


# parse the file name on the command line, and get all the related file names
file_names, year, month, day, hour, minute = get_file_names(file_name)

# open all the input files
files = []
for file_name in file_names:
    try:
        files.append(file(file_name, 'r'))
    except IOError:
        pass


# open output file
output_filename = 'RV-8_Data_' + year + '-' + month + '-' + day + '-' + hour\
   + minute + '.txt'

if output_dir != '':    
    output_filename = output_dir + '/' + output_filename
    
output = open(output_filename, 'w')

# create date string for the header of the output file
date = time.strftime('%H:%M %d %b %Y', (int(year), int(month), int(day),\
   int(hour), int(minute), 1, 1, 1, 1))

header, blank_data = get_header(files)
output.write(header)

# The line_cache holds data lines that are not used, but would be useful later.
# The process to determine the earliest start time reads the first line in each
# file, but the first line in some files could be much later than the time at
# which the data recording starts.  Thus those lines may need to be cached.
# The line_cache is necessary because each line in the data file can only be 
# read once, unless the index point in the file is reset.
#
# The line_cache_time holds the time stamp for each line in the line_cache, so 
# it only needs to determined once.  The line_cache_flag is true if there is an
# unused line in the line cache for that device.
#
line_cache = []
line_cache_time = []
line_cache_flag = [False, False, False, False]

start_time_raw = get_start_time(files)

# Determine the data rate of the original data
# Determine if the discretes data rate is higher than the selected data rate
discretes_file_id = get_file_id('Discretes')
discretes_data_rate = get_data_rate(files[discretes_file_id])

if data_rate == 0:
    # default to the original data rate, if the desired data rate was not given
    data_rate = discretes_data_rate

start_time_orig = int(float(start_time_raw) * data_rate) / data_rate
next_time = start_time_orig + 1 / data_rate

# Determine if the discretes data rate is higher than the selected data rate
# discretes_file_id = get_file_id('Discretes')
# discretes_data_rate = get_data_rate(files[discretes_file_id])

if discretes_data_rate > data_rate:
# #     # we must treat the discretes data carefully to be sure to not miss an 
# #     # event that happens for a short period, in between the times when we
# #     # will pull the discretes data
    files[discretes_file_id] = make_temp_discretes(files[discretes_file_id], start_time_orig, data_rate)
else:
    # need to advance the file to the correct spot
    for x in range(number_of_header_lines):
        files[discretes_file_id].readline()



print 'Processing the data file.  This should only take a few seconds.'
while 1:
    # write first line
    offset = start_time_orig
    line_out = process_time_slice(start_time_orig, next_time, offset)
    output.write(line_out)
    
    # process remaining lines
    count = 1
    
    while 1:
#   for x in range(1900):
        start_time = start_time_orig + count / data_rate
        next_time = start_time + 1 / data_rate
        line_out = process_time_slice(start_time, next_time, offset)
        if line_out == None:
            print 'No line out.'
            break
        output.write(line_out)
        count += 1
        
    break