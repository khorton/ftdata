#! /sw/bin/python2.4

# script to merge data files from Grand Rapids EIS 4000 engine monitor, 
# Dynon D-10A EFIS, Garmin GNS-430 GPS and a discrete event marker into 
# a single file. 

import re
# from test import list

#------------------------------------------------------------------------------#
#
# Define and parse command line options
#
#------------------------------------------------------------------------------#

def get_options():
	from optparse import OptionParser
	parser = OptionParser()
	parser.usage = "%prog [options] file_name"
	parser.add_option("-i", "--input", dest="input", 
					  help="Define one of the input files.", metavar="input files")
	parser.add_option("-o", "--output", dest="output", 
					  help="Define output directory.  Default is the script directory", metavar="output directory")
	# parser.add_option("-q", "--quiet",
	#                   action="store_false", dest="verbose", default=True,
	#                   help="don't print status messages to stdout")
	
	(options, args) = parser.parse_args()
	
	# if not (args or options.input):
	#    parser.error('Error - You must supply one of the input file names.\nThe file name can either be bare after the script name, or it can be given following an "-i"')
	
	if args:
		file_name = args[0]
	elif options.input:
		file_name = options.input
	else:
		parser.error('Error - You must supply one of the input file names.\nThe file name can either be bare after the script name, or it can be given following an "-i"')
	
	print 'The file name is:', file_name
	
	if options.output:
		output_dir = options.output
		print 'Output directory defined as', output_dir
	else:
		output_dir = ''
	
	return file_name

#------------------------------------------------------------------------------#
#
# Get file names
#
# Given the name of one input file, get the other names.
#------------------------------------------------------------------------------#

def get_file_names(file_name):
	file_data = re.search('_data-([0-9]{4})-([0-9]{2})-([0-9]{2})-([0-9]{4})\.txt',file_name)
	try:
		(year, month, day, time) = file_data.groups()
	except:
		print 'The file name is not in the expected format.  It must look like device_data_yyyy_mm_dd_time.txt'
		return
	print 'Year:', year, 'month:', month, 'day:', day, 'time:', time
	
	list = ['EIS4000', 'D10A', 'GNS430', 'Discretes']
	
# 	print list

	file_names = []
	n = 0
	for n in range(len(list)):
		file_names.append(list[n] + '_data-' + str(year) + '-' + str(month) + '-' + str(day) + '-' + str(time) + '.txt')
		print file_names[n]

	return file_names




file_name = get_options()
file_names = get_file_names(file_name)
print 'File names are:', file_names

files = []
for file_name in file_names:
	files.append(file(file_name, 'r'))

print 'Files are:', files

num_files = len(files)

data = []
for n in range(num_files):
	for r in range(500):
		data[n].append(files[n].readline())

for n in range(num_files):
	print data[n][2]