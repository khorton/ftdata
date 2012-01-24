#!/usr/bin/perl
#
# Perl script to record data from a Garmin GNS 430.  High resolution computer
# time is appended to each data record to facilitate time sync with other data.
#
# Two Perl modules are required: Device::SerialPort and Time::HiRes.  
#
# This script was tested on Apple OS X 10.3.7 with perl 5.8.1, but it should
# work on any Unix type OS.
#
# Data comes from one of the RS-232 outputs, with the GNS 430 "Channel Output"
# configured to "Aviation".  The data format is detailed in Appendix C of the
# Garmin 400 Series Installation Manual.  
#
# Wiring - The RS-232 OUT wire is connected to pin 2 of the DB-9 connector at
#          the serial port.  The RS-232 IN wire is connected to pin 3 of the
#          DB-9 connector at the serial port.
#
# The GNS 430 outputs Type 1 and Type 2 sentences on the RS-232.  
# The Type 1 sentences include: 
#   GPS altitude,
#   Latitude and Longitude,
#   Track,
#   Ground Speed,
#   Distance to waypoint,
#   Cross Track Error,
#   Desired Track,
#   To Waypoint Identifier,
#   Bearing to To Waypoint,
#   Magnetic Variation, 
#   Nav Flag Status, and
#   Distance to Destination Waypoint.
#   
# The Type 2 Sentences provide a list of all waypoints in the flight plan, with
# their latitude, longitude and magnetic variation.  
#
# All of the Type 1 sentences are recorded, except:
#   Bearing to Waypoint,
#   Magnetic Variation,
#   Nav Flag Status, and
#   Distance to Destination
# Waypoint.  None of the Type 2 sentences are recorded.
#
# MUST DO - The following items must be completed by the user, or the script
#           will not function.
# 
# 1. The script must be editted to set the "$SCRIPT_HOME" variable to the path
#    to the script.
#
# 2. The serial port must be specified on lines 2 and 22 of the "GNS.config"
#    file. The rest of this file should be left as-is.
#
# 3. The GNS.config file must be located in the same location as the script,
#    or the variable "$config_file" must be set to the config file location.
#
# 4. Ensure the script permissions are set to be exectuable.  In the terminal,
#    run the following command "chmod a+x GNS_data_capture.pl".
#
# 5. Ensure the config file can be read. In the terminal, run the following
#    command "chmod a+r GNS.config".
#
# HOW TO RUN THE SCRIPT
#
# 1. Connect the GNS 430 to the computer, using a USB to Serial adapter if
#    required.
#
# 2. Turn on the GNS 430.
#
# 3. In the terminal, run "GNS_data_capture.pl" to record at the default data
#    rate.  If something other than the default data rate is desired, run 
#    "GNS_data_capture.pl n" where "n" is the desired  data rate in records per
#    second.  E.g., for two records per second, run "GNS_data_capture.pl 2".
#    For one record every 5 seconds (i.e. 0.2 records per second), run 
#    "GNS_data_capture.pl 0.2".
#
# 4. To stop data capture, type "Ctrl-C".
#    
# To do - 1. Add code for Windows, with automatic detection of the OS.
#
#         2. Add selectable record separator to data config file.
#
#         3. Ensure $data_from_file is set to 0 prior to release.
#
#         4. Rework command line switch to be -r X -d Y, where X is the data
#            rate and Y is the duration in minutes.
#
#         5. Test what happens if the GNS is turned OFF then ON during a data
#            capture.  May need to greatly increase the timeout in GNS.config.
#
#         6. Consider moving serial port parametres into the main script, and
#            dropping the GNS.config file.  This may make the script more
#            portable with Windows.
#
# Author - Kevin Horton - khorton01@rogers.com
#
# The author is not an experienced perl programmer.  Experienced perl
# programmers would have written a much shorter, more efficient script.  But
# the script works.  Please send any suggested improvements to the author.
#
# This script is free software; you can redistribute it and/or modify it under
# the same terms as Perl itself.
#
# Rev 0.001, 1251Z 15 Oct 05
#
###############################################################################


use warnings;
use strict;
no locale;

use Time::HiRes qw( time sleep );
use Cwd;

use vars qw( $OS_win );
# Detect Operating system and load appropiate serial port module
BEGIN {
   $OS_win = ($^O eq "MSWin32") ? 1 : 0;
   if ($OS_win) {
      eval "use Win32::SerialPort";
      die "$@\n" if ($@);
   }
   else {
      eval "use Device::SerialPort";
      die "$@\n" if ($@);
   }
} # End BEGIN

###############################################################################
# Define variables

# uncomment the following line to manually input the script location, if the
# Cwd module is not available.
# my $SCRIPT_HOME = "/Users/my_user_dir/ftdata/EFIS";

# comment out the following line if the Cwd module is not available
my $SCRIPT_HOME = &Cwd::cwd();

my $DATA_FILE_LOCATION = $SCRIPT_HOME;
# If desired, specifiy data file location by uncommenting and editting the
# following line.
#my $DATA_FILE_LOCATION = "/Users/my_user_dir";

#my $GNS_data_config = "$SCRIPT_HOME/GNS_data.config";
my $config_file = "$SCRIPT_HOME/GNS.config";
my $config_file_present = "1";
my $data_from_file = "1";	# 1 = read from raw data file for testing.  
                            # 0 = read from GNS 430
my $OUTPUT_FILE = "";
my $output_file_header ="";
my $duration = "600";       # length of time to record data in minutes
my $block_size = "110";     # Type 1 sentences total about 105 bytes.
                            # 110 bytes is the minimum to ensure that the two
                            # byte header is present, no matter where the
                            # header starts in the read.

my $data_file_name = "";	# name data file by device, date and time.
my $data_rate = "1";		# number of records per sec
my $count = "";				# time x datarate, so that need to read one record
                            # every time count increments by one
my $data_time = "";			# time that each data slice is read
my $data_count = "";		# data time x datarate
my $match_start = "";		# first part of data block
my $match_end = "";			# second part of data block

my $DES = "\t";				# Data element separator - what goes after each
                            # item in a line of data.
                            
                            # \t is a tab character.  You might want a comma
                            #instead, e.g. my $DES = ",";

my $RES = "\n";				# Record end separator - i.e. the line ending

                            # tab = \t
                            # line feed = \n
                            # carriage return = \r

                            # Unix-like systems (including Macintosh OS X and 
                            # Linux) use \n as the line ending.
                            # DOS and MS Windows use \r\n as the line ending.
                            # Macintosh OS 9 and earlier use \r as the line 
                            # ending.
###############################################################################

# get date/time to make data file name
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdat) = localtime(time);

# pad months, days, hours and minutes to get two digits if required
if ($mday < 10) {
  $mday = "0$mday";
}

# unix months start at 0
$mon = $mon + 1;

if ($mon < 10) {
  $mon = "0$mon";
}

if ($hour < 10) {
  $hour = "0$hour";
}

if ($min < 10) {
  $min = "0$min";
}

$year = $year + 1900;

$data_file_name = "EIS_data-$year-$mon-$mday-$hour$min.txt";

$OUTPUT_FILE = "$SCRIPT_HOME/$data_file_name";

if ( $data_from_file == "0" ) {
  # Define with tied filehandle
  my $GNSPort = tie(*GNS,'Device::SerialPort', "$config_file")
    || die "Can't tie: $!\n";
} else {
  open(*EIS,"<","$SCRIPT_HOME/GNS-HT-2004-05-11-0649.TXT");
}

###############################################################################
# check to see if there is a command line switch.  If so, set the data rate.
if ($#ARGV >= 0) {
  $data_rate = $ARGV[0];
}

print "Logging GNS 430 data.  Press Ctrl-C to abort. \n";

open (OUTPUT , '>' , "$OUTPUT_FILE")
  or die "Can't open test data file out: $!";
binmode OUTPUT;
  
# output header to start the file
print OUTPUT "$data_file_name$RES$RES";
print OUTPUT "$output_file_header$RES";

$count = int(time * $data_rate);

my $start_time = time;
my $i = "0";
while (time < ($start_time + $duration * 60)) {
  if ($data_from_file == "1"){
    sleep(0.2);
  }
  $i++;
  my $data = "";
  $data_time = time;

  read(GNS,$data,"$block_size");
  $data_count = $data_time * $data_rate;
  
  # Is it time to record another block of data?
  if ($data_count >= $count) {
  
   # Search for text with hex(02) at beginning and hex(03) at end
   # marking the beginning and end of a frame of data
#    ($match_start) = ($data =~ /\xfe\xff\xfe(.{0,70})/s);
   ($match_start) = ($data =~ m/\x02.+?\x03/so);

###############
        
    # if $match_start is too short, grab another chunck, which has the rest of
    # the data record
    if (length($match_start) < "$block_size") {
      read(GNS,$data,"$block_size");
    
      # find the rest of the data record, which ends with the next three byte
      # header
      ($match_end) = ($data =~ /(.{0,70})\xfe\xff\xfe/s);
    
      # assemble the two pieces into a full record
      $data = $match_start . $match_end;
    } else {
      $data = $match_start;
    }

#     my $checksum = unpack("%8C*", $data);
#     if ($checksum == 255) {
      my ($GPS_Alt, $Lat_Deg, $Lat_Min, $Long_Deg, $Long_Min, $Track, $GS, 
        $Dist_to_Wpt, $XTK, $DTK, $Dest_Wpt, $Bearing_to_Dest_Wpt, $mag_Var,
        $Nav_Flag_Status, $Warning_Status, $Dist_to_Dest_Wpt) = 
      unpack ('nnnnnnnnnnnnnnnnnnnCCccnCnnnnnnnCCCCCnnCC' , $data);

            
#    scaling
     my $latitude = $Lat_Deg + $Lat_Min/60;
     my $longitude = $Long_Deg + $Long_Min/60;
     $Dist_to_wpt = $Dist_to_Wpt/10;
     $XTK = $XTK/100;
     $DTK = $DTK/10;
     
     
     
      print OUTPUT join( "\t", @data{ @variable_list } ), "\n";
      $count++;
#     } else {
#       print "bad checksum with record $i\n";
#     }
  }
}




close OUTPUT
  or die "Can't close test data file out: $!";
  
# Destroy GNS filehandle
undef $GNSPort;
untie *GNS;

exit;

