# Module to read GPS data in NEMA 0183 format
# Reads both the $GPGGA and $GPRMC data words.
# For use with FRD.pl main program
#
# Copyright ?/?/?, ??
# License ?
#
# Tested using Magellan SportTrak Map handheld GPS unit
# which
#
# Release / Change History
# Still in alpha test stage
# Only the GPRMC word is being decoded at this time

# Need to verify that the proper values are returned.
#   Convert knots to m/s, and any other conversions
#   Checksum is not being calculated or verified at this time
#

use warnings;
use strict;

package NMEA0183v2;
# package is a unique name for each type of device you want to read 
# Multiple devices of the same type can be read from different 
# comm ports. This is also the device name that will be referenced
# through out this module and the name which will appear on the device list
# the user selects

my ($device_name) = __PACKAGE__;

# Add device name to list of available devices
push(@main::device_list, $device_name);

# What fields will be recorded and in what order for each device
$main::devices{$device_name}{'fields'} = ['date', 'utc time', 'lat', 'lat dir', 'long', 'long dir', 'alt', 'spd', 'track'];

$main::devices{$device_name}{'units'}{'date'} = 'dd-mm-yyyy';
$main::devices{$device_name}{'units'}{'time'} = 'hh:mm:ss.sss';
$main::devices{$device_name}{'units'}{'lat'} = 'deg';
$main::devices{$device_name}{'units'}{'lat dir'} = '';
$main::devices{$device_name}{'units'}{'long'} = 'deg';
$main::devices{$device_name}{'units'}{'long dir'} = '';
$main::devices{$device_name}{'units'}{'alt'} = 'm';
$main::devices{$device_name}{'units'}{'spd'} = 'm/s';
$main::devices{$device_name}{'units'}{'track'} = 'm';

# Serial port configuration
$main::devices{$device_name}{'portconfig'}{'baudrate'} = 4800;
$main::devices{$device_name}{'portconfig'}{'parity'} = 'none';
$main::devices{$device_name}{'portconfig'}{'databits'} = 8;
$main::devices{$device_name}{'portconfig'}{'stopbits'} = 1;
$main::devices{$device_name}{'portconfig'}{'handshake'} = 'none';

# Reference of subroutine below to interpret the serial data
$main::devices{$device_name}{'sub'} = \&read_NEMA0183; 

# This function needs to be defined
sub calc_checksum {
   my ($data) = @_;
   
   return("xx");
}

sub read_NEMA0183 {
   my ($dev_num, $input_data) = @_;

   if (!defined($input_data)) {
      return "";
   }
   
   my ($format);
   my (@data_array);
   my ($line_GPGGA, $whats_leftover_GPGGA, $checksum_GPGGA);
   my ($line_GPRMC, $whats_leftover_GPRMC, $checksum_GPRMC);
   my ($time, $junk, $day, $month, $year, $deg, $min);
   my ($utc_time, $status, $lat, $lat_dir, $long, $long_dir, $spd, $track, $date) = 0;
   my ($mag_var, $mag_var_dir, $gpsmode) = 0;

   # End of messase characters that is sent by device.
   # DO NOT use the \n code as this changes with different operating systems
   my ($eol) = "\x0D\x0A"; # CR LF
   
#   @data_array = ($input_data =~ m/\$GPGGA[0-9\+\-a-zA-Z.,*]+$eol/go); # fills data_array with matches to format
#   $whats_leftover_GPGGA = $'; # Perl special variable that holds everything AFTER the last match
#   $line_GPGGA = $&; # Perl special variable that holds the last matched data pattern
#   $checksum_GPGGA = calc_checksum($line_GPGGA);

   @data_array = ($input_data =~ m/\$GPRMC[0-9\+\-a-zA-Z.,*]+$eol/go); # fills data_array with matches to format
   $whats_leftover_GPRMC = $'; # Perl special variable that holds everything AFTER the last match
   $line_GPRMC = $&; # Perl special variable that holds the last matched data pattern
   $checksum_GPRMC = calc_checksum($line_GPRMC);

   # Make sure that BOTH GPRMC and GPGGA words have been received befor decoding data
   # Return full line and do not decode if both words are not part of frame.
#   if (($line_GPRMC eq '') or ($line_GPGGA eq '')) {
#      return(($input_data);
#   }
   
   if (defined($line_GPRMC)) {
      # Decode line of GPS GPRMC data frame
      ($junk, $utc_time, $status, $lat, $lat_dir, $long, $long_dir, $spd, $track, $date
         , $mag_var, $mag_var_dir, $gpsmode) = split(/,/ , $line_GPRMC);
      
      # Convert data to default units
      ($day, $month, $year) = unpack('A2 A2 A2', $date);
      $date = sprintf("%02.0f/%02.0f/%04.0f", $day, $month, $year+2000);
      $utc_time = sprintf("%02.0f:%02.0f:%02.0f", unpack('A2 A2 A2', $utc_time));
      ($deg, $min) = unpack('A2 A20', $lat);
      $lat = $deg + $min/60;
      ($deg, $min) = unpack('A3 A20', $long);
      $long = $deg + $min/60;
      $spd = $spd * 1; # Need to convert knots to m/s

      # Save data into global data hash table
      # Include ALL available data, even if you do not intend to use it at this time
      # The parameters to be saved will come from this list
      
      $main::data{$dev_num}{'date'} = $date;
      $main::data{$dev_num}{'utc time'} = $utc_time;
      $main::data{$dev_num}{'lat'} = $lat;
      $main::data{$dev_num}{'lat dir'} = $lat_dir;
      $main::data{$dev_num}{'long'} = $long;
      $main::data{$dev_num}{'long dir'} = $long_dir;
      # $main::data{$dev_num}{'alt'} = 'm'; #altitude not available in GPRMC data frame
      $main::data{$dev_num}{'spd'} = $spd;
      $main::data{$dev_num}{'track'} = $track;

   }
   else {
      # no match found, return ALL data
      return($input_data);
   }
   
#   if (length($whats_leftover_GPGGA) < length($whats_leftover_GPRMC)) {
#      return($whats_leftover_GPGGA);
#   }

   return $whats_leftover_GPRMC;
   
   # Include explination of format
   # $GPRMC Output Sentence: example
   # $GPRMC,180432,A,4027.027912,N,08704.857070,W,000.04,181.9,131000,1.8,W,D*25
   # Field  Value     Meaning
   # 1   180432       UTC of position fix in hhmmss format (18 hours, 4 minutes and 32 seconds)
   # 2   A            Status (A - data is valid, V - warning)
   # 3   4027.027912  Geographic latitude in ddmm.mmmmmm format (40 degrees and 27.027912 minutes)
   # 4   N            Direction of latitude (N - North, S - South)
   # 5   08704.857070 Geographic longitude in dddmm.mmmmmm format (87 degrees and 4.85707 minutes)
   # 6   W            Direction of longitude (E - East, W - West)
   # 7   000.04       Speed over ground (0.04 knots)
   # 8   181.9        Track made good (heading) (181.9º)
   # 9   131000       Date in ddmmyy format (October 13, 2000)
   # 10  1.8          Magnetic variation (1.8º)
   # 11  W            Direction of magnetic variation (E - East, W - West)
   # 12  D            Mode indication (A - autonomous, D - differential, N - data not valid)   
}

# The following line MUST be included
1;