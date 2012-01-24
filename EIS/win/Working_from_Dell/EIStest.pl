#!/usr/bin/perl
#
# Perl script to grab a block of data from a Grand Rapids EIS
#
# tested using the Keyspan adapter on the Dell on 23 Jan 05.
# appears to work correctly.  Data file is EIS_data-2005-01-23-1647.dat
# 
# It is notable that all parametres are specified in this file, rather
# than using a config file.  Is this significant?

use warnings;
#use strict;
no locale;
use Time::HiRes qw( time sleep );

#my $HOME = "/Users/tmh/Kevin/ftdata";
my $OUTPUT_FILE = "";
my $config_file = "";
my $cycles = "10";
my $block_size = "2000";
my $data_file_name = "";	# name data file by device, date and time.
my $data_file = "";


#BEGIN {
#        $OS_win = ($^O eq "MSWin32") ? 1 : 0;
#        if ($OS_win) {
#            eval "use Win32::SerialPort 0.19";
#            $config_file = "c:\\ftdata\\eis\\eis3.config";
#            $data_file_name = "EIS_data-$year-$mon-$mday-$hour$min.txt";
#            $data_file = "c:\\ftdata\\eis\\$data_file_name";
#	    die "$@\n" if ($@);
#        }
#        else {
#            eval "use Device::SerialPort";
#            $HOME = "/Users/kwh";
#            $config_file = "$HOME/.ftdata/EFIS.config";
#            $data_file_name = "EFIS_data-$year-$mon-$mday-$hour$min.txt";
#            $data_file = "$HOME/.ftdata/$data_file_name";            
#	    die "$@\n" if ($@);
#        }
#} # End BEGIN


# get date/time to make data file name
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

my $data_file_name = "EIS_data-$year-$mon-$mday-$hour$min.dat";

  use Win32::SerialPort;
  $OUTPUT_FILE = "c:\\ftdata\\eis\\$data_file_name";
  $config_file = "c:\\ftdata\\eis\\eis4.config";

# Define with tied filehandle
#my $EISPort = tie(*EIS,'Win32::SerialPort', "$config_file")
#  || die "Can't tie: $!\n";

$EISPort = new Win32::SerialPort("COM4");

$EISPort-> databits(8);
$EISPort-> baudrate(9600);
$EISPort-> parity("none");
$EISPort-> stopbits(1);
  
# timeouts (from demo6.plx in tarball)
#$EISPort->read_char_time(200);
#$EISPort->read_char_time(200);
#$EISPort->read_const_time(1000);

# other parameters (from demo6.plx in tarball)
$EISPort->error_msg(1);		# use built-in error messages
$EISPort->user_msg(1);
#$EISPort->stty_icrnl(1);		# depends on terminal
#$EISPort->stty_echo(0);		# depends on terminal


open (OUTPUT , '>' , "$OUTPUT_FILE")
  or die "Can't open test data file out: $!";

binmode OUTPUT;

for (my $i = 1; $i <= $cycles; $i++) {
  print "In the loop $i\n";
  my $data = "";
#  $data = $EISPort->read($block_size);
  (my $count_in, $data) = $EISPort->read("$block_size");
  warn "read unsuccessful\n" unless ($count_in == $block_size);
  print "Block size = $block_size, Read bytes = $count_in\n";
  print OUTPUT "$data";

}
close OUTPUT
  or die "Can't close test data file out: $!";
  
# Destroy EIS filehandle
undef $EISPort;
#untie *EIS;

exit;

