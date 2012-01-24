# Module to read data from Dynon Avionics EFIS-D10A
# 
# For use with FRD.pl main program
#
# Copyright ?/?/?, ??
# License ?
#
# Tested with ??, firmware ver??
#
# Release / Change History
# Still in alpha testing stage
#

# Need to verify that the proper values are returned.
#         decode lines of each frame.
#         save data to hash
#         Convert knots to m/s

use warnings;
use strict;

package D10A;
# package is a unique name for each type of device you want to read 
# Multiple devices of the same type can be read from different 
# comm ports. This is also the device name that will be referenced
# through out this module and the name which will appear on the device list
# the user selects

my ($device_name) = __PACKAGE__;

# Add device name to list of available devices
push(@main::device_list, $device_name);

# What fields will be recorded and in what order for each device
$main::devices{$device_name}{'fields'} = ['time', 'pitch', 'roll', 'yaw', 'spd', 'alt', 'turn rate', 'g lat', 'g vert', 'aoa'];

$main::devices{$device_name}{'units'}{'time'} = 'hh:mm:ss.sss';
$main::devices{$device_name}{'units'}{'pitch'} = 'deg';
$main::devices{$device_name}{'units'}{'roll'} = 'deg';
$main::devices{$device_name}{'units'}{'yaw'} = 'deg';
$main::devices{$device_name}{'units'}{'spd'} = 'm/s';
$main::devices{$device_name}{'units'}{'alt'} = 'm';
$main::devices{$device_name}{'units'}{'turn rate'} = 'deg/s';
$main::devices{$device_name}{'units'}{'g lat'} = 'g';
$main::devices{$device_name}{'units'}{'g vert'} = 'g';
$main::devices{$device_name}{'units'}{'aoa'} = '%stall angle';

# Serial port configuration
$main::devices{$device_name}{'portconfig'}{'baudrate'} = 115200;
$main::devices{$device_name}{'portconfig'}{'parity'} = 'none';
$main::devices{$device_name}{'portconfig'}{'databits'} = 8;
$main::devices{$device_name}{'portconfig'}{'stopbits'} = 1;
$main::devices{$device_name}{'portconfig'}{'handshake'} = 'none';

# Reference of subroutine, in this file, to interpret the serial data
$main::devices{$device_name}{'sub'} = \&read_D10A; 

sub read_D10A {
   my ($dev_num, $input_data) = @_;

   if (!defined($input_data)) {
      return "";
   }
 
   my ($format);
   my ($line, @data_array, $whats_leftover);

   my ($hr, $min, $sec, $sec_frac, $pitch, $roll, $yaw, $spd, $alt) = 0;
   my ($turn_rate, $g_lat, $g_vert, $aoa, $crlf) = 0;

   # Refer to perl's pack and unpack functions for explanation of format
   $format = "A2 A2 A2 A2 A4 A5 A3 A4 A5 A4 A3 A3 A2 A2";   

   my ($eol) = "\x0D\x0A"; # CR LF

   @data_array = ($input_data =~ m/[0-9\+\-]{41}$eol/go); # fills data_array with matches to format

   $whats_leftover = $'; # Perl special variable that holds everything AFTER the last match
   $line = $&; # Perl special variable that holds the last matched data pattern

   if (defined($line) and (length($line) == length(pack($format, '')))) {
      # Decode line of serial data
      ($hr, $min, $sec, $sec_frac, $pitch, $roll, $yaw, $spd, $alt,
         $turn_rate, $g_lat, $g_vert, $aoa, $crlf) = unpack($format, $line);
      
      # Convert data to default units
      $sec = $sec + ($sec_frac/64);
      $pitch = $pitch / 10;
      $roll = $roll / 10;
      $spd = $spd / 10; # meters/sec
      $turn_rate = $turn_rate / 10;
      $g_lat = $g_lat / 10;
      $g_vert = $g_vert / 10;
      
     
      # Save data into global data hash table
      # Include ALL available data, even if you do not intend to use it at this time
      # The parameters to be saved will come from this list
      $main::data{$dev_num}{'time'} = "$hr:$min:$sec";
      $main::data{$dev_num}{'pitch'} = $pitch;
      $main::data{$dev_num}{'roll'} = $roll;
      $main::data{$dev_num}{'yaw'} = $yaw;
      $main::data{$dev_num}{'spd'} = $spd;
      $main::data{$dev_num}{'alt'} = $alt;
      $main::data{$dev_num}{'turn rate'} = $turn_rate;
      $main::data{$dev_num}{'g lat'} = $g_lat;
      $main::data{$dev_num}{'g vert'} = $g_vert;
      $main::data{$dev_num}{'aoa'} = $aoa;
   }
   else {
      # no match found, return ALL data
      return($input_data);
   }
   
   return($whats_leftover); # Return whats left from data stream, will be used during next scan
   
   # Include explination of format
   # From the EFIS-D10A manual dated 7/6/2004
   # The EFIS-D10A outputs text data through its serial port constantly during normal operation. This data is useful for a
   # variety of applications. All numbers are in decimal and are standard ASCII. To view the data using a terminal program,
   # the following settings should be used:
   # Baud rate: 115200
   # Data: 8 bit
   # Parity: none
   # Stop: 1 bit
   # Flow control: none
   # The format for the data being sent out the RS232 port is:
   # Start Width Description Notes
   # 1      2    Hour 00 to 23, current hour according to EFIS-D10A’s internal clock
   # 3      2    Minute 00 to 59, current minute according to EFIS-D10A’s internal clock
   # 5      2    Second 00 to 59, current second according to EFIS-D10A’s internal clock
   # 7      2    Fractions 00 to 63, counter for 1/64 second. Data output frequency.
   # 9      1    Pitch Sign ‘+’ or ‘-’ (positive means plane is pitched up)
   # 10     3    Pitch 000 to 900, pitch up or down from level flight in 1/10 degrees (900 = 90 Degs)
   # 13     1    Roll Sign ‘+’ or ‘-’ (positive means plane is banked right)
   # 14     4    Roll 0000 to 1800, roll left or right from level flight in 1/10 degrees (1800 = 180 Degs)
   # 18     3    Yaw 000 to 359 in degrees (000 = North, 090 = East, 180 = South, 270 = West)
   # 21     4    Airspeed 0000 to 9999, airspeed in units of 1/10 m/s (1555 = 155.5 m/s)
   # 25     1    Altitude Sign ‘+’ or ‘-’ (positive means altitude is above sea-level)
   # 26     4    Altitude 0000 to 9999, altitude in units of meters
   # 30     1    Turn Rate Sign ‘+’ or ‘-’ (positive means plane is turning right)
   # 31     3    Turn Rate 000 to 999, 1/10 degrees/second rate of yaw change
   # 34     1    Lateral G’s Sign ‘+’ or ‘-’ (positive means plane is experiencing leftward lateral acceleration)
   # 35     2    Lateral G’s 00 to 99, lateral G’s in units of 1/10 G (99 = 9.9 G’s)
   # 37     1    Vertical G’s Sign ‘+’ or ‘-’ (positive means plane is experiencing upward vertical acceleration)
   # 38     2    Vertical G’s 00 to 99, vertical G’s in units of 1/10 G (99 = 9.9 G’s)
   # 40     2    Angle of Attack 00 to 99, percentage of stall angle.   
   # 42     2    CR/LF Carriage Return, Linefeed = 0x13, 0x10
}

# The following line MUST be included and should be the last line in the file
1;