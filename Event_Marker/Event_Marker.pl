#!/usr/bin/perl
#
# Test to see if Device::SerialPort can be used to monitor an event marker
#
# Perl script to record up to four discretes.  High resolution computer time 
# is appended to each data record to facilitate time sync with other data.
# The signal is sensed when there is voltage on the pin in question.
#
# Use one signal for an event marker, one for boost pump (to look for coorelation
# between boost pump ON, fuel pressure and fuel flow).
#
# This version simply prints to screen, as a test.
#
# MUST DO - The following items must be completed by the user, or the script
#           will not function.
# 
# 1. The script must be editted to set the "$SCRIPT_HOME" variable to the path
#    to the script.
#
# 2. The serial port must be specified next to the $PortName variable in this
#    file. The rest of this file should be left as-is.
#
# 3. Connect up to four discretes plus a ground to the pins of a DB-9 
#    connector.
#
#      Pin 1 - discreted sensed by MS_RLSD_ON message.
#      Pin 5 - ground.
#      Pin 6 - discreted sensed by MS_DSR_ON message.
#      Pin 8 - discreted sensed by MS_CTS_ON message.
#      Pin 9 - discreted sensed by MS_RING_ON message.
#
# 4. Ensure the script permissions are set to be exectuable.  In the terminal,
#    run the following command "chmod a+x Discretes.pl".
#
# HOW TO RUN THE SCRIPT
#
# 1. Connect the discretes to the computer, using a USB to Serial adapter if
#    required.
#
# 2. In the terminal, run "Discretes.pl" to record at the default data
#    rate.  If something other than the default data rate is desired, run 
#    "Discretes.pl n" where "n" is the desired  data rate in records
#    per second.  E.g., for 2 records per second, run "Discretes.pl 2".
#    For one record every 5 seconds (i.e. 0.2 records per second), run 
#    "Discretes.pl 0.2".
#
#
# TO DO 1. Add code to write to file.
#
#       2. Add code to control data rate.
#
#       3. Test.
#
# Author - Kevin Horton - kevin01@kilohotel.com
#
# The author is not an experienced perl programmer.  Experienced perl
# programmers would have written a much shorter, more efficient script.  But
# the script works.  Please send any suggested improvements to the author.
#
# This script is free software; you can redistribute it and/or modify it under
# the same terms as Perl itself.
#
# Rev 34 2000Z 09 Mar 2005
#
###############################################################################

BEGIN {
        our $OS_win = ($^O eq "MSWin32") ? 1 : 0;
        if ($OS_win) {
            eval "use Win32::SerialPort 0.19";
	    die "$@\n" if ($@);
        }
        else {
            eval "use Device::SerialPort";
	    die "$@\n" if ($@);
        }
} # End BEGIN

use strict;
use warnings;

#use Device::SerialPort qw( :STAT );
use Time::HiRes qw( time sleep );

# Define parametres
my $SCRIPT_HOME = "/Users/kwh/ftdata/Event_Marker";
my $PortName = "/dev/tty.USA49W3b1P4.4";

my $duration = "300";                     # run duration, in minutes
my $now_time = "0";
my $data_file_name_prefix = "Discretes";  # Prefix for data file name

my $data_file_name = "";                  # name data file by device, date and time.
my $data_rate = "4";                      # default number of records per second to record.
my $OUTPUT_FILE = "";


# check to see if there is a command line switch.  If so, set the data rate.
if ($#ARGV >= 0) {
  $data_rate = $ARGV[0];
}

print "Logging discretes.  Press Ctrl-C to abort. \n";

# if ($OS_win) {
#   my $Discretes = new Win32::SerialPort ( $PortName )
#        || die "Can't open $PortName: $!\n";
# } else {
  my $Discretes = new Device::SerialPort ( $PortName )
       || die "Can't open $PortName: $!\n";
# }

# open filehandle for data file
$data_file_name = "$data_file_name_prefix . -. Get_Date_Time()";
$OUTPUT_FILE = "$SCRIPT_HOME/$data_file_name";

open (OUTPUT , '>' , "$OUTPUT_FILE")
  or die "Can't open test data file out: $!";


# output header
print OUTPUT "$data_file_name\n\n";
print OUTPUT "Computer Time\tEvent Marker\tEIS Warn\tBoost Pump\tDiscrete 4\n";


my $start_time = time;
while (time < ($start_time + $duration * 60)) {
	$now_time = time;
	my $ModemStatus = $Discretes->modemlines;
	#   if ($ModemStatus & $Discretes->MS_CTS_ON) { 
	#     print "$now_time\tevent marker detected *************\n"; 
	#   } else {
	#     print "$now_time\tnada\n";
	#   }
	
	print "$now_time\t
	$ModemStatus & $Discretes->MS_RLSD_ON\t
	$ModemStatus & $Discretes->MS_DSR_ON\t
	$ModemStatus & $Discretes->MS_CTS_ON\t
	$ModemStatus & $Discretes->MS_RING_ON\n"; 

	sleep 0.1;
}

exit;

sub Get_Date_Time {
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdat) = localtime(time);
	
	# pad months, days, hours and minutes to get two digits if required
	if ($mday < 10) {
	  $mday = "0$mday";
	}
	
	$mon = $mon + 1;
	
	# pad months to get two digits if required
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
	my $date_time = "$year-$mon-$mday-$hour$min.txt";
	return $date_time;

}