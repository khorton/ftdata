#!/usr/bin/perl
#
# Perl script to record serial data from a Dynon D-10A EFIS.  High resolution
# computer time is appended to each data record to facilitate time sync with
# other data.
#
# This script works with Dynon software version 2.11 on the D-10A.  Earlier
# software versions had a shorter data stream that is not compatible with this
# version of the script.
#
# Three Perl modules are required: 
#
# 1. Time::HiRes (may be part of the standard perl distribution)
#
# 2. Cwd (may be part of the standard perl distribution).  If the Cwd module is
#    not available, the script location can be manually specified in the code.
#    See the comments in the code for more info.
#
#
# 3. Device::SerialPort (OS X or Unix/Linux) or Win32::SerialPort (Windows).
#    Win32::SerialPort is not part of the standard Activestate distribution of 
#    perl for Win32
#
#    An OS X packaage for Device::SerialPort is available via the Fink
#    package distribution system (http://fink.sourceforge.net/).
#
# This script was tested on Apple OS X 10.4.2 with perl 5.8.6, but it should
# work on any Unix type OS.
#
# The data parametres to be recorded, their labels and scaling, are specified
# in the EFIS_data.config file.  The default location of this file is the same 
# directory as this script.  This can be changed by specifying a new location
# with the variable "$EFIS_data.config".
#
################################################################################
# 
# WIRING
# 
# The EFIS must be connected to the computer serial port as follows:
# 
#       EFIS               Computer
#     Connector           Serial Port
#    DB-25 Female         DB-9 Female
#      Pin 9 <-------------> Pin 5
#      Pin 10 <------------> Pin 2
#      Pin 22 <------------> Pin 3
#      
###############################################################################
#
# MUST DO - The following items must be completed by the user, or the script
#           will not function.
# 
# 1. The serial port must be specified on lines 2 and 22 of the "EFIS.config"
#    file. The rest of this file should be left as-is.
#
# 2. The EFIS.config file must be located in the same location as the script,
#    or the variable "$config_file" must be set to the config file location.
#
# 3. Ensure the script permissions are set to be exectuable.  In the terminal,
#    run the following command "chmod a+x EFIS_data_capture.pl".
#
# 4. Ensure both data files can be read. In the terminal, run the following
#    command "chmod a+r EFIS_data.config EFIS.config".
#
###############################################################################
#
# SHOULD DO - The following items should be completed, but the script will use
#             default values if they are not completed.
#
# 1. Copy the "EFIS_data.config" file to the same location as the script, or 
#    set the variable "$EFIS_data_config" to the location of the file.
#    EFIS_data.config NOT YET IMPLEMENTED.
#
# 2. Edit the "EFIS_data.config" file to set the desired default data rate, the
#    list of variables to record, the order to record them, the labels and
#    units to put in the file header, and the scaling factors to use.  The
#    default recording duration can also be specified.
#
#    If the "EFIS_data.config" file is not found, the script will use a default
#    data rate of one record per second, record every variable, in a default
#    order, with headers the same name as the variables, and no scaling. The
#    data units will be as described in the EFIS User's Guide.
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
# 1. Connect the EFIS to the computer, using a USB to Serial adapter if
#    required.
#
# 2. Turn on the EFIS.
#
# 3. In the terminal, run "EFIS_data_capture.pl" to record at the default data
#    rate.  If something other than the default data rate is desired, run 
#    "EFIS_data_capture.pl n" where "n" is the desired  data rate in records
#    per second.  E.g., for 2 records per second, run "EFIS_data_capture.pl 2".
#    For one record every 5 seconds (i.e. 0.2 records per second), run 
#    "EFIS_data_capture.pl 0.2". 
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
#         1. Add a loop to monitor the keyboard, and quit when ESC is pressed.
#
#         2. Check code for detection of Windows, and add this functionality
#            for config and data file locations.
#
#         3. Add selectable record separator to data config file.
#
#         4. Ensure $data_from_file is set to 0 prior to release.
#
#         5. Rework command line switch to be -r X -d Y, where X is the data
#            rate and Y is the duration in minutes.
#
#         6. Done.
#
#         7. Consider moving serial port parametres into the main script, and
#            dropping the EFIS.config file.  This may make the script more
#            portable with Windows.
#
#        8. Add code to specify the interval at which the data file should be
#           written to disk.
#
###############################################################################
#
# DONE  - The following TO DO items have been completed.
#
#         6. Test what happens if the EFIS is turned OFF then ON during a data
#            capture.  OK.  Tested on 9 Oct.  Get an error on the Terminal
#            screen, but the script keeps running, and it recovers OK once the
#            EFIS is back ON.  The script records garbage data while the EFIS
#            is OFF, but it is quite obvious that the data is no good.
#
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
# Rev 1 10 Oct 2005
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
my $EFIS_data_config = "$SCRIPT_HOME/EFIS_data.config";
my $config_file = "$SCRIPT_HOME/EFIS.config";
my $config_file_present = "1";
my $data_from_file = "0";	# 1 = read from raw data file for testing.  
                            # 0 = read from EFIS
my $OUTPUT_FILE = "";
my $output_file_header ="";
my $duration = "300";       # length of time to record data in minutes
my $interval = "1";
my @lines = ();             # array of lines in the data config file
my %record = ();            # hash of which parametres to record
my @parametres = ();        # array of parametres in desired order
my @labels = ();            # list of desired parametre labels
my %scaling = ();           # hash of parametre scalings
my %units = ();             # hash of parametre units
my @scaling_list = ();      # array of parametres with scalings other than 1
my @variable_list = ();     # holds list of variables to be output to data file
my $data_file_name = "";    # name data file by device, date and time.
my $option = "";            # option to select data rate
my $data_rate = "4";        # default number of records per second to record.
my $count = "";				# time x datarate, so that need to read one record
                            # every time count increments by one
my $data_time = "";			# time that each data slice is read
my $data_count = "";		# data time x datarate

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
open (DATA_CONFIG , '<' , "$EFIS_data_config")
  or $config_file_present = 0;
  
# if the data config file is present, but not readable, alert the user.
if (-e $EFIS_data_config) {
  if (-r $EFIS_data_config != "1") {
    print "The data config file exists, but it is not readable.  Check the file permissions.\n";
  }
}

if ($config_file_present == 1) {
  @lines=<DATA_CONFIG>;
#  print "@lines";
  
  foreach my $line (@lines) {
    if ($line !~ /^[#\s]/) {
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
  
  ### remove!!! - used to record a quick burst of data for ASI calibration
#  $duration = "0.25";
  
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
  $output_file_header = "Computer Time$DES EFIS Hour$DES EFIS Minute$DES EFIS Second$DES EFIS Counter$DES Pitch$DES Roll$DES Heading$DES IAS$DES Altitude$DES Turn Rate$DES Ny$DES Nz$DES AOA$DES Status Bit Mask$DES Product ID$RES";

  @variable_list = qw(data_time Hour Minute Second Counter Pitch Roll Heading IAS Altitude Turn_Rate Ny Nz AOA Status_Bit_Mask Product_ID);
  
}


###############################################################################
# check to see if there is a command line switch.  If so, set the data rate.
if ($#ARGV >= 0) {
  $data_rate = $ARGV[0];
}

print "Logging EFIS data.  Press Ctrl-C to abort. \n";

if ( $data_from_file == "0" ) {
  my $EFISPort = tie(*EFIS,'Device::SerialPort', "$config_file")
    || die "Can't tie: $!\n";
  $EFISPort->read_const_time(100);       # const time for read (milliseconds)
  $EFISPort->read_char_time(0);          # avg time between read char
  $EFISPort->linesize(41)
} else {
  open(*EFIS,"<","$SCRIPT_HOME/EFIS_15_mn_1-22-05.data");
}

# open filehandle for data file
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
$data_file_name = "EFIS_data-$year-$mon-$mday-$hour$min.txt";
$OUTPUT_FILE = "$DATA_FILE_LOCATION/$data_file_name";

open (OUTPUT , '>' , "$OUTPUT_FILE")
  or die "Can't open test data file out: $!";


# output header
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

  # read one line of data
  $data = <EFIS>;
  $data_count = $data_time * $data_rate;

  # Is it time to record another block of data?
  if ($data_count >= $count) {
  
    # test for correct length data block
    if ( (length ( $data ) ) == 53 ) {
      my ($Hour, $Minute, $Second, $Counter, $Pitch, $Roll, $Heading, $IAS, $Altitude,
      $Turn_Rate, $Ny, $Nz, $AOA, $Status_Bit_Mask, $Product_ID, $DataCheckSum) = unpack ('A2 A2 A2 A2 A4 A5 A3 A4 A5 A4 A3 A3 A2 A6 A2 A2' , $data);

      # get decimal checksum of the first 49 bytes
      my $CalcCheckSum = unpack("%8C49", $data);
      
      # convert the hex checksum in the data stream to decimal
      $DataCheckSum = hex($DataCheckSum);
      
      if ( $DataCheckSum == $CalcCheckSum ) {
        # scale data
#         $Pitch = $Pitch/10;
#         $Roll = $Roll/10;
#         $IAS = $IAS * 0.1943846; # convert from tenths of meter/sec to knots
#         $Altitude = $Altitude/0.3048; # convert from meters to feet
#         $Turn_Rate = $Turn_Rate/10;
#         $Ny = $Ny/100;
#         $Nz = $Nz/10;
#         $AOA = $AOA/100;

# Convert data to a hash, to facilitate using the config file.
# There is probably a much cleaner way to do all this, but this way works.
      my %data = (
      data_time => $data_time,
           Hour => $Hour,
         Minute => $Minute,
         Second => $Second,
        Counter => $Counter,
          Pitch => $Pitch,
           Roll => $Roll,
        Heading => $Heading,
            IAS => $IAS,
       Altitude => $Altitude,
      Turn_Rate => $Turn_Rate,
            AOA => $AOA,
             Ny => $Ny,
             Nz => $Nz,
Status_Bit_Mask => $Status_Bit_Mask,
     Product_ID => $Product_ID,
       );

      foreach (@scaling_list) {
        $data{ $_ } *= $scaling{ $_ };
      }
  
#        print OUTPUT "$data_time\t$Hour\t$Minute\t$Second\t$Counter\t$Pitch\t$Roll\t$Heading\t$IAS\t$Altitude\t$Turn_Rate\t$Ny\t$Nz\t$AOA\n";
      print OUTPUT join( "$DES", @data{ @variable_list } ), "$RES";
      } else {
        print "Bad checksum with record  $i\n";
      }

      $count++;
    }
  }
}

# Destroy EFIS filehandle
if ( $data_from_file == "0" ) {
  undef my $EFISPort;
}
untie *EFIS;
