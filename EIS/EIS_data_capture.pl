#!/usr/bin/perl
#
# Perl script to record data from a Grand Rapids EIS.  High resolution computer
# time is appended to each data record to facilitate time sync with other data.
#
# Three Perl modules are required: 
#
# 1. Time::HiRes (may be part of the standard perl distribution)
#
# 2. Cwd (may be part of the standard perl distribution).  If the Cwd module is
#    not available, the script location can be manually specified in the code.
#    See the comments in the code for more info.
#
# 3. Device::SerialPort (OS X or Unix/Linux) or Win32::SerialPort (Windows).
#    Win32::SerialPort is not part of the standard Activestate distribution of 
#    perl for Win32
#
#    An OS X packaage for Device::SerialPort is available via the Fink
#    package distribution system (http://fink.sourceforge.net/).
#
# This script was tested on Apple OS X 10.4.2 with perl 5.8.6, but it should
# work on any Unix type OS.  It may work on Windows with Active State Perl, but
# it has not neen tested.
#
# The data parametres to be recorded, their labels and scaling, are specified
# in the EIS_data.config file.  The default location of this file is the same 
# directory as this script.  This can be changed by specifying a new location
# with the variable "$EIS_data.config".
#
################################################################################
# 
# WIRING
# 
# The EIS 4000 must be connected to the computer serial port as follows:
# 
#                                  Computer
#                                 Serial Port
#                                 DB-9 Female
#    Ground <----------------------> Pin 5
# EIS 4000 Pin 9 <-----------------> Pin 2
#  14 V Power <--------------------> Pin 6
#  
###############################################################################
#
# MUST DO - The following items must be completed by the user, or the script
#           will not function.
# 
# 1. The serial port must be specified on lines 2 and 22 of the "EIS.config"
#    file. The rest of this file should be left as-is.
#
# 2. The EIS.config file must be located in the same location as the script,
#    or the variable "$config_file" must be set to the config file location.
#
# 3. Ensure the script permissions are set to be exectuable.  In the terminal,
#    run the following command "chmod a+x EIS_data_capture.pl".
#
# 4. Ensure both config files can be read. In the terminal, run the following
#    command "chmod a+r EIS_data.config EIS.config".
#
###############################################################################
#
# SHOULD DO - The following items should be completed, but the script will use
#             default values if they are not completed.
#
# 1. Copy the "EIS_data.config" file to the same location as the script, or 
#    set the variable "$EIS_data_config" to the location of the file.
#
# 2. Edit the "EIS_data.config" file to set the desired default data rate, the
#    list of variables to record, the order to record them, the labels and
#    units to put in the file header, and the scaling factors to use.  The
#    default recording duration can also be specified.
#
#    If the "EIS_data.config" file is not found, the script will use a default
#    data rate of one record per second, record every variable, in a default
#    order, with headers the same name as the variables, and no scaling. It
#    will record data for 10 hours, and stop.
#
# 3. Change the default Data Element Separator and Record End Separator, if
#    necessary to match what your spreadsheet or graphing program expects. The
#    default is to use a Tab to separate data fields, and a line Feed between
#    records.
#
# 4. Specify an alternate data file location, if desired.  The default data
#    file location is the same location as the script.
#
###############################################################################
#
# HOW TO RUN THE SCRIPT
#
# 1. Connect the EIS to the computer, using a USB to Serial adapter if
#    required.
#
# 2. Turn on the EIS.
#
# 3. In the terminal, run "EIS_data_capture.pl" to record at the default data
#    rate.  If something other than the default data rate is desired, run 
#    "EIS_data_capture.pl n" where "n" is the desired  data rate in records per
#    second.  E.g., for two records per second, run "EIS_data_capture.pl 2".
#    For one record every 5 seconds (i.e. 0.2 records per second), run 
#    "EIS_data_capture.pl 0.2".
#
# 4. To stop data capture, type "Ctrl-C".  The data is only flushed to disk
#    periodically - if you hit "Ctrl-C" before any data has been written, no
#    data will be written at all.
#
# 5. The data file will be saved in the same location as the script, unless the
#    $DATA_FILE_LOCATION variable in the script is editted to specify a 
#    different location.
#
###############################################################################
#
# TO DO - The following changes may someday be added to the script.
#
#         1. improve recovery from bad checksum - try to pass over the start of
#            the next record, to minimize the time delay for the replacement
#            record.
#
#            Very low priority, as bad checksums seem effectively to never
#            occur when connected to EIS.  They happen very rarely when testing
#            with a raw data file as the input.
#
#         2. Test on Windows.
#
#         3. Use selectable record separator from data config file. This must
#            specifed in the main file for now.
#
#         4. Ensure $data_from_file is set to 0 prior to release.
#
#         5. Rework command line switch to be -r X -d Y, where X is the data
#            rate and Y is the duration in minutes.
#
#         6. Done
#
#         7. Consider moving serial port parametres into the main script, and
#            dropping the EIS.config file.  This may make the script more
#            portable with Windows.
#
#         8. Done
#
#         9. Done
#
#        10. Add code to specify the interval at which the data file should be
#            written to disk.
#
###############################################################################
#
# DONE  - The following TO DO items have been completed.
#
#         6. Test what happens if the EIS is turned OFF then ON during a data
#            capture.  May need to greatly increase the timeout in EIS.config.
# 
#            Tested on 2 Oct 2005 - There seems to be no problem with starting
#            the script, then turning on the EIS, or with cycling the EIS
#            power with the script running.  It takes the EIS a few data 
#            records for the data to stabilize, but the script doesn't care.
#
#         8. Add code to read the units from the data_config file and put them
#            in the header.  
#
#            Tested on 8 Oct 2005.
#
#         9. Add code to detect the path to the script, to avoid the need to 
#            specify the "$SCRIPT_HOME" variable.
#
#            Tested on 3 Oct 2005 on OS X 10.4.2 with perl 5.8.6.  The Cwd
#            module was present as part of the basic perl installation.
#
###############################################################################
#
# Author - Kevin Horton - khorton01@rogers.com
#
# The author is not an experienced perl programmer.  Experienced perl
# programmers would have written a much more efficient script.  But the script
# works.  Please send any suggested improvements to the author.
#
# This script is free software. You can redistribute it and/or modify it under
# the same terms as Perl itself.
#
# Rev 1, 10 Oct 2005
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
my $EIS_data_config = "$SCRIPT_HOME/EIS_data.config";
my $config_file = "$SCRIPT_HOME/EIS.config";
my $config_file_present = "1";
my $data_from_file = "0";	# 1 = read from raw data file for testing.  
                            # 0 = read from EIS-4000
my $OUTPUT_FILE = "";
my $output_file_header ="";
my $duration = "600";       # length of time to record data in minutes
my $block_size = "75";      # 75 bytes is the minimum to ensure that the three 
                            # byte header is present, no matter where the
                            # header starts in the read.
my @lines = ();             # array of lines in the data config file
my %record = ();            # hash of which parametres to record
my @parametres = ();        # array of parametres in desired order
my @labels = ();            # list of desired parametre labels
my %scaling = ();           # hash of parametre scalings
my %units = ();             # hash of parametre units
my @scaling_list = ();      # array of parametres with scalings other than 1
my @variable_list = ();     # holds list of variables to be output to data file
my %data = ();              # holds all engine monitor data
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
# read data config file, and set parametres
open (DATA_CONFIG , '<' , "$EIS_data_config")
  or $config_file_present = 0;
  
# if the data config file is present, but not readable, alert the user.
if (-e $EIS_data_config) {
  if (-r $EIS_data_config != "1") {
    print "The data config file exists, but it is not readable.  Check the file permissions.\n";
  }
}

if ($config_file_present == 1) {
  @lines=<DATA_CONFIG>;
  #print "@lines";
  
  foreach my $line (@lines) {
    if ($line !~ /^[#\s]/) {
  #   print $line;
  
  # extract default data rate
      if ($line =~ /^default\sdata\srate\s\=\s\b(.+)$/) {
        $data_rate = $1;
      }
  
  # extract default recording duration
      if ($line =~ /^default\sduration\s\=\s\b(.+)$/) {
        $duration = $1;
      }
  
  # extract which parametres are to be recorded
      if ($line =~ /^(\w+)\s+Record.+([01])/) {
        $record{$1} = $2;
      }
      
  # extract the parameter order, labels and units
      if ($line =~ /^(\w+)\s+Label\s\=\s\b(.+)\b\s+Units\s\=\s\b(.+)$/) {
        push @parametres,$1;
        push @labels,$2;
        $units{$2} = $3;
      }
  
  # extract parametre scaling
      if ($line =~ /^(\w+)\s+Scaling\s\=\s\b(.+)$/) {
        $scaling{$1} = $2;
      }
    }
  }      


  # set header for output file, according to info in the data config file.
  # also sets list of variables to be recorded
  $output_file_header = "Time$DES";
  
  # create array with just the parametres to be recorded, in order
  $variable_list[0] = "data_time";
  for (my $i = 0; $i < @parametres; $i++) {
    if ($record{$parametres[$i]} == 1) {
      $output_file_header = $output_file_header . $labels[$i] . "$DES";
      push @variable_list, $parametres[$i];
    }
  }
 
 # add a second line to the header with the units
 # append record end separator to the first line
 $output_file_header = $output_file_header . "$RES" . "seconds" . "$DES";
 
  for (my $i = 0; $i < @parametres; $i++) {
    if ($record{$parametres[$i]} == 1) {
      $output_file_header = $output_file_header . "(" . $units{$labels[$i]} . ")" . "$DES";
    }
  }
 
 
  # create array with just the parametres to be scaled
  for (my $i = 0; $i < @parametres; $i++) {
    if ($scaling{$parametres[$i]} != 1) {
      push @scaling_list, $parametres[$i];
    }
  }
} else {
  # set defaults for header and variable list if config file not found
  print "The data config file was not read.  Default values will be used.\n";
  $output_file_header = "Time$DES RPM$DES CHT 1$DES CHT 2$DES CHT 3$DES CHT 4$DES CHT 5$DES CHT 6$DES EGT 1$DES EGT 2$DES EGT 3$DES EGT 4$DES EGT 5$DES EGT 6$DES DAUX 1$DES DAUX 2$DES Airspeed$DES Altitude$DES Volt$DES Fuel Flow$DES Unit Temp$DES Carb Temp$DES Rate of Climb$DES OAT$DES Oil Temp$DES Oil Press$DES Aux 1$DES Aux 2$DES Aux 3$DES Aux 4$DES Water Temp$DES Hour Meter$DES Fuel Qty$DES Hrs$DES Min$DES Sec$DES Hours End$DES Min End$DES Altimeter$DES Heading$RES";

  @variable_list = qw(data_time TACH CHT1 CHT2 CHT3 CHT4 CHT5 CHT6 EGT1 EGT2 EGT3 EGT4 EGT5 EGT6 DAUX1 DAUX2 ASPD ALT VOLT FUEL_FLOW UNIT_TEMP CARB ROCSGN OAT OILT OILP AUX1 AUX2 AUX3 AUX4 COOL ETI QTY HRS MIN SEC ENDHRS ENDMIN BARO MAGHD);
  
}

###############################################################################
# check to see if there is a command line switch.  If so, set the data rate.
if ($#ARGV >= 0) {
  $data_rate = $ARGV[0];
}

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

$OUTPUT_FILE = "$DATA_FILE_LOCATION/$data_file_name";

if ( $data_from_file == "0" ) {
  # Define with tied filehandle
  my $EISPort = tie(*EIS,'Device::SerialPort', "$config_file")
    || die "Can't tie: $!\n";
} else {
  open(*EIS,"<","$SCRIPT_HOME/EIS_15_mn_1-22-05.data");
}

print "Logging Engine Monitor data.  Press Ctrl-C to abort. \n";


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
  read(EIS,$data,"$block_size");
  $data_count = $data_time * $data_rate;
  
  # Is it time to record another block of data?
  if ($data_count >= $count) {
  
    # find three byte header, plus the rest of the read
    ($match_start) = ($data =~ /\xfe\xff\xfe(.{0,70})/s);
        
    # if $match_start is too short, grab another chunck, which has the rest of
    # the data record
    if (length($match_start) < "70") {
      read(EIS,$data,"$block_size");
    
      # find the rest of the data record, which ends with the next three byte
      # header
      ($match_end) = ($data =~ /(.{0,70})\xfe\xff\xfe/s);
    
      # assemble the two pieces into a full record
      $data = $match_start . $match_end;
    } else {
      $data = $match_start;
    }

    my $checksum = unpack("%8C*", $data);
    if ($checksum == 255) {
      my ($TACH, $CHT1, $CHT2, $CHT3, $CHT4, $CHT5, $CHT6,
        $EGT1, $EGT2, $EGT3, $EGT4, $EGT5, $EGT6, $DAUX1, 
        $DAUX2, $ASPD, $ALT, $VOLT, $FUEL_FLOW, $UNIT_TEMP,
        $CARB, $ROCSGN, $OAT, $OILT, $OILP, $AUX1, $AUX2, 
        $AUX3, $AUX4, $COOL, $ETI, $QTY, $HRS, $MIN, $SEC,
        $ENDHRS, $ENDMIN, $BARO, $MAGHD, $SPARE, $CHKSUM) = 
      unpack ('n19 C c3 n C n7 C5 nnCC' , $data);

# Convert data to a hash, to facilitate using the config file.
# There is probably a much cleaner way to do all this, but this way works.
%data = (
   data_time => $data_time,
        TACH => $TACH,
        CHT1 => $CHT1,
        CHT2 => $CHT2,
        CHT3 => $CHT3,
        CHT4 => $CHT4,
        CHT5 => $CHT5,
        CHT6 => $CHT6,
        EGT1 => $EGT1,
        EGT2 => $EGT2,
        EGT3 => $EGT3,
        EGT4 => $EGT4,
        EGT5 => $EGT5,
        EGT6 => $EGT6,
       DAUX1 => $DAUX1,
       DAUX2 => $DAUX2,
        ASPD => $ASPD,
         ALT => $ALT,
        VOLT => $VOLT,
   FUEL_FLOW => $FUEL_FLOW,
   UNIT_TEMP => $UNIT_TEMP,
        CARB => $CARB,
      ROCSGN => $ROCSGN,
         OAT => $OAT,
        OILT => $OILT,
        OILP => $OILP,
        AUX1 => $AUX1,
        AUX2 => $AUX2,
        AUX3 => $AUX3,
        AUX4 => $AUX4,
        COOL => $COOL,
         ETI => $ETI,
         QTY => $QTY,
         HRS => $HRS,
         MIN => $MIN,
         SEC => $SEC,
      ENDHRS => $ENDHRS,
      ENDMIN => $ENDMIN,
        BARO => $BARO,
       MAGHD => $MAGHD,
       );
            
      foreach (@scaling_list) {
        $data{ $_ } *= $scaling{ $_ };
      }

      print OUTPUT join( "$DES", @data{ @variable_list } ), "$RES";
      $count++;
    } else {
      print "bad checksum with record $i\n";
    }
  }
}
close OUTPUT
  or die "Can't close test data file out: $!";
  
# Destroy EIS filehandle
if ( $data_from_file == "0" ) {
  undef my $EISPort;
}
untie *EIS;

exit;

