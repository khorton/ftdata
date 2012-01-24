#!/usr/bin/perl

use Time::HiRes qw( time sleep );

use strict;
use warnings;

my ($OS_win, @coms, $i);
my ($filename, $serialport, $baudrate, $serial, $data);

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

if (@ARGV == 3) {
   $filename = $ARGV[0];
   $serialport = $ARGV[1];
   $baudrate = $ARGV[2];
   
   $serial = open_com_port($serialport);
   
   if (!defined($serial)) {
      print "\n\nCould not open serial port $serialport\n";
      exit;
   }
   
   $serial->baudrate("$baudrate");
   $serial->databits('8');
   $serial->parity('none');
   $serial->stopbits('1');
   $serial->write_settings;

   # Read all old data and throw it away
   $data = $serial->input();
   
   open(DATAFILE, ">$filename") or die "Could not open $filename";
   
   print "Port $serialport opened, writing data to file $filename\n";
   print "Press Ctrl-C to exit\n";

   my $start_time = time;
   my $end_time = $start_time + 60;
   my $now_time = time;
   while($now_time < $end_time) {
      $data = $serial->input();
      print DATAFILE $data;
      $now_time = time;
   }
}
else {
   print "usage: serialcapture.pl filename portname baudrate\n\n";
   print "Detecting serial ports\n";
   @coms = detect_commports();
   if (defined($coms[0])) {
      print "Serial ports detected:\n";
      foreach $i (@coms) {
         print "  $i\n";
      }
   }
   else {
      print "No serial ports detected\n";
   }
}
   
exit;

sub detect_commports {
   # Tries to autodetect available serial comm ports
   # Returns list (array) of available serial ports

   # Linux/Unix section needs to be tested.

   my ($i, $port, $porthandle, @portlist, $quiet, @searchlist);

   $quiet = 1; # Prevents error messages from being printed to STDERR during detection

   @portlist = ();
   @searchlist = ();

   if ($OS_win) {
      # For Windows machines
      for ($i=1 ; $i <= 8 ; $i++){
         $port = 'COM' . $i;
         push(@searchlist, $port);
      }
   }
   else {
      # Get list of all potential serial devices for UNIX/Linux/OS-X machines
      push(@searchlist, </dev/tty.*>);
      push(@searchlist, </dev/ttyS*>);
   }

   foreach $port (@searchlist) {
      if ($OS_win) {
         $porthandle = Win32::SerialPort->new ($port, $quiet);
      }
      else {
         $porthandle = Device::SerialPort->new ($port, $quiet);
      }

      if ($porthandle) {
         # Valid port detected, add it to list
         $porthandle->close;
         push(@portlist, $port);
      }
      else {
         # Not a valid port or it is open by another application
      }
      undef $porthandle;
   }

   return (@portlist);
}

sub open_com_port {
   my ($port) = @_;

   my ($porthandle, $command);

   if ($OS_win) {
      $porthandle = Win32::SerialPort->new ($port);
   }
   else {
      $porthandle = Device::SerialPort->new ($port);
   }
   
   return $porthandle;

}

