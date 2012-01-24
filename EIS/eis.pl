#!/usr/bin/perl
#
# Perl script to grab a block of data from a Grand Rapids EIS
#
# 13 Jan 05
#
# Seems to work.  Saves block of data to binary file.
# had to remove code to check for Win or Mac.  This script is hard-wired to Win.
# Next step - graft in code that decodes the data, and saves a text file with hi-res times

use warnings;
#use strict;
no locale;

my $HOME = "/Users/kwh";
my $OUTPUT_FILE = "";
my $config_file = "";
my $cycles = "25";
my $block_size = "255";

$OS_win = ($^O eq "MSWin32") ? 1 : 0;


#BEGIN {
#        $OS_win = ($^O eq "MSWin32") ? 1 : 0;
#        if ($OS_win) {
#            eval "use Win32::SerialPort 0.19";
#            $config_file = "c:\\ftdata\\eis\\eis3.config";
#	    die "$@\n" if ($@);
#	    # Define with tied filehandle
#	    my $EISPort = tie(EIS,'Win32::SerialPort', "$config_file")
#	      || die "Can't tie: $!\n";
#print "in WIN32\n";
#        }
#        else {
#            eval "use Device::SerialPort";
#            $config_file = "$HOME/.ftdata/EFIS.config";
#	    die "$@\n" if ($@);
#	    # Define with tied filehandle
#	    my $EISPort = tie(EIS,'Device::SerialPort', "$config_file")
#	      || die "Can't tie: $!\n";
#        }
#} # End BEGIN

#use Win32::SerialPort;
use Device::SerialPort;
#$config_file = "c:\\ftdata\\eis\\eis3.config";
$config_file = "$HOME/ftdata/EIS/pb/EIS.config";
#die "$@\n" if ($@);
# Define with tied filehandle
#my $EISPort = tie(EIS,'Win32::SerialPort', "$config_file")
my $EISPort = tie(*EIS,'Device::SerialPort', "$config_file")
  || die "Can't tie: $!\n";




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

if ($OS_win) {
  $data_file = "c:\\ftdata\\eis\\$data_file_name";
} else {
  $data_file = "$HOME/ftdata/EIS/$data_file_name";
}


## Initialize variables as required for Windows or Mac OS X
#my $OS_win = ($^O eq "MSWin32") ? 1 : 0;
#if ($OS_win) {
#  $OUTPUT_FILE = "c:\\ftdata\\$data_file_name";
#}
#else {
#  $OUTPUT_FILE = "/Users/tmh/Kevin/ftdata/EIS/$data_file_name";
#  $config_file = "$HOME/EIS.config";
#}

  
# timeouts (from demo6.plx in tarball)
$EISPort->read_char_time(2);
$EISPort->read_const_time(200);

# other parameters (from demo6.plx in tarball)
$EISPort->error_msg(1);		# use built-in error messages
$EISPort->user_msg(1);
$EISPort->stty_icrnl(1);		# depends on terminal
$EISPort->stty_echo(0);		# depends on terminal


open (OUTPUT , '>' , "$data_file")
  or die "Can't open test data file out: $!";

binmode OUTPUT;

for (my $i = 1; $i <= $cycles; $i++) {
print "run $i\n";
  my $data = "";
  $data = $EISPort->read($block_size);
#  $data = $EISPort->read(2000);
#  sysread(*EIS,$data,$block_size);
  print OUTPUT "$data";

}
close OUTPUT
  or die "Can't close test data file out: $!";
  
# Destroy EIS filehandle
undef $EISPort;
untie *EIS;

exit;

