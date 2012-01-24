#!/usr/bin/perl
#
# Test to see if Device::SerialPort can be used to monitor an event marker
#
# works with MS_RLSD_ON for a  signal on pin 1, with ground as pin 5
# works with MS_DSR_ON for a  signal on pin 6, with ground as pin 5
# works with MS_CTS_ON for a  signal on pin 8, with ground as pin 5
# works with MS_RING_ON for a  signal on pin 9, with ground as pin 5
#
# So, could in principle use one serial port to monitor up to four discretes
# The signal is sensed when there is voltage on the pin in question.
#
# This version simply prints to screen, as a test.
#
# TO DO 1. Add code to write to file.  For the moment, only pin 8 is wired as
#          event marker.  So we only need to look for MS_CTS_ON, and put a "1"
#          to the file if this is detected, and a "0" if it is not detected.

use strict;
use warnings;

use Device::SerialPort qw( :STAT );
use Time::HiRes qw( time sleep );

my $duration = ".25"; # run duration, in minutes
my $now_time = "0";

my $PortName = "/dev/tty.USA49W1b1P4.4";
my $EventMarker = new Device::SerialPort ( $PortName )
       || die "Can't open $PortName: $!\n";
       
my $start_time = time;
while (time < ($start_time + $duration * 60)) {
  $now_time = time;
  my $ModemStatus = $EventMarker->modemlines;
  if ($ModemStatus & $EventMarker->MS_CTS_ON) { 
    print "$now_time\tevent marker detected *************\n"; 
  } else {
    print "$now_time\tnada\n";
  }
  sleep 0.1;
}

exit;