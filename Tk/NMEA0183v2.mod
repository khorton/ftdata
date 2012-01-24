# Module to read GPS data in NEMA 0183 format
# Reads both the $GPGGA and $GPRMC data words.
# For use with sdl.pl main program
#
# Copyright Michael Ketterman, 2005
#
# License: This is free software that may be used for any purpose.
#
# No warranty or fitness for any particular application is guaranteed.
# User assumes all risk for using this software.
#
# Release status:
# This software is in the early stages of development and may be broken.
#
# Tested using Magellan SportTrak Map handheld GPS unit
#
#
# Release / Change History
# Still in alpha test stage
# Only the GPRMC word is being decoded at this time

use warnings;
use strict;

package NMEA0183v2 ;
# package is a unique name for each type of device you want to read
# Multiple devices of the same type can be read from different
# comm ports. This is also the device name that will be referenced
# through out this module and the name which will appear on the device list
# the user selects from

my ($device_name) = __PACKAGE__;

# Add device name to list of available devices
#push(@main::device_list, $device_name);

# Version info will have special meaning in the future
my $version = 0.2; # must be numeric
my $date = 'dd mmm yyyy';

# Detect of Win32 system
my $OS_win = ($^O eq "MSWin32") ? 1 : 0;

my @fields = ('date', 'utc_time', 'lat', 'lat_dir'
  , 'long', 'long_dir', 'alt', 'spd', 'track', 'checksum');

my %chan_label = (
  'date'    => 'Date',
  'utc_time' => 'UTC Time',
  'lat'    => 'Lat',
  'lat_dir'  => 'Lat Direction',
  'long'    => 'Long',
  'long_dir' => 'Long Dir',
  'alt'    => 'Alitude',
  'spd'    => 'Speed',
  'track'   => 'Track',
  'checksum' => 'Checksum',
);

my %units = (
  'date'    => 'dd-mm-yyyy',
  'time'    => 'hh:mm:ss.sss',
  'lat'    => 'deg',
  'lat dir'  => '',
  'long'    => 'deg',
  'long dir' => '',
  'alt'    => 'm',
  'spd'    => 'm/s',
  'track'   => 'm',
);

# hash array containing configuration for serial port
# Names MUST match only valid settings for port as all items
# will be writtem to configuration routine exactly as they appear here
my (%portconfig) = (
  'baudrate'  =>  $main::config_data{$device_name}{baudrate},
  'databits'  => '8',
  'parity'   => 'none',
  'stopbits'  => '1',
  'handshake' => 'none',
);

sub config_screen {
  # Each device must define its own configurtion/setup screen and place
  # it into a new tab of the notebook widget.
  
  my ($class, $nb) = @_;

  my $row = 0;
  my $col = 0;
  
  my $page_ref = {};
  $page_ref->{page} = $nb->add($device_name, -label => $device_name);  

#  $page_ref->{page}->Label(
#    -text => "Channels to Use",
#  )->grid(-row => $row, -column=> $col);
#
#  $row++;
#
#  $page_ref->{listbox} = $page_ref->{page}->Scrolled('Listbox',
#    -scrollbars => 'e',
#    -selectmode => 'multiple',
#    -exportselection => '0',
#  )->grid(-row => $row, -column=> $col, -padx => 10, -rowspan => 10);
#
#  # Fill listbox with fields from module
#  $page_ref->{listbox}->insert('end', @fields);
#
#  $row += 10;
#  
#  $page_ref->{page}->Button(
#    -text => "Select All Channels",
#    -command => sub {  },
#  )->grid(-row => $row, -column=> $col, -pady=>3);
#
#  $row = 2;
#  $col++;
  
  my $config_item;
  
  my (@baudrates) = (115200, 57600, 56000, 38400,
     19200, 14400, 9600, 4800, 2400, 1200, 300);
  
  # Baudrate dropdown selection box
  $page_ref->{page}->Label(-text=>'Baud rate')
     ->grid(-row=>$row, -column=>$col, -sticky=>'e');
  $page_ref->{page}->BrowseEntry(
     -choices => \@baudrates,
     -variable => \$main::config_data{$device_name}{baudrate},
     -width => 8,  
  )->grid(-row=>$row++, -column=>$col+1, -pady=>3, -sticky=>'w');
     
  # Simulated data from file 
  $page_ref->{page}->Label(-text=>"Simulated Input\nFile Name")
     ->grid(-row=>$row, -column=>$col, -sticky=>'e');
  $page_ref->{page}->Entry(
     -textvariable => \$main::config_data{$device_name}{simfile},
     -width => '20',
  )->grid(-row=>$row++, -column=>$col+1, -pady=>3, -sticky=>'w');
  
}

sub config_save {
   # DO NOT change the name of this function
   # Each module will define how to save its configuration data in the future
   my ($self) = @_;
   my ($config) = '';
   
   my ($key, $val);
   while (($key, $val) = each(%{$main::config_data{$device_name}})) {
      $config .= "$key=>'$val', ";
   }
   $config .= "\n";
   
   return($config);
}

sub new {
  # DO NOT change the name of this function
  my $class = shift;
  my $self = {};
  # Load default values
	$self->{device} = $device_name;
	@{$self->{'fields'}} = @fields;
	%{$self->{'units'}} = %units;
	%{$self->{'portconfig'}} = %portconfig;
	%{$self->{'label'}} = %chan_label;

	$self->{'porttype'} = 'serial';
	
	%{$self->{'data'}} = ();
	
	$self->{'input_data'} = "";
	
	$self->{version} = $version;
	$self->{date} = $date;

	$self->{dev_num} = -1;
	
	# Set default values, function defined later in module
   $main::config_data{$device_name} = set_default_values();
	
	bless $self;
	
	return $self;
}

sub open_comm_port {
  # DO NOT change the name of this function
  my ($self, $port) = @_;
  my ($porthandle);   

  # Both methods needed for cross platform compatability
  if ($OS_win) {
   $porthandle = Win32::SerialPort->new($port);
  }
  else {
   $porthandle = Device::SerialPort->new($port);
  }

  $self->{porthandle} = $porthandle;
}

sub read_comm_port {
  # DO NOT change the name of this function
  my ($self) = @_;

  if (defined($self->{porthandle})) {
   return $self->{porthandle}->input();
  }
  else {
    return;
  }
}

sub close_comm_port {
  # DO NOT change the name of this function
  my ($self) = @_;

  if (defined($self->{porthandle})) {
   $self->{porthandle}->close();
  }
}

sub calc_nmea_checksum {
  my ($frame) = @_;
  my ($data, $frame_cs, $char, $i, $length, $calc_cs);

  ($data, $frame_cs) = split(/\*/o, $frame); # split on the '*' character
  $frame_cs = hex(substr($frame_cs, 0, 2)); # numeric value of hexadecimal checksum

  $length = length($data);
  $calc_cs = '';
  for ($i = 1; $i < $length ; $i++) {
    $calc_cs ^= $char = substr($data, $i, 1); # xor characters together
  }

  if ($frame_cs == ord($calc_cs)) {
    return(1); # Checksum matches
  }
  else {
    return(0); # Checksum dosn't match
  }
}

sub decode_data {
  # DO NOT change the name of this function
  my ($self, $new_data) = @_;
  if (!defined($new_data)) {
    return;
  }
  
  my ($input_data);
  
  $self->{input_data} .= $new_data;
  
  $input_data = $self->{input_data};

  my ($format);
  my (@data_array);
  my ($line_GPGGA, $whats_leftover_GPGGA, $checksum_GPGGA);
  my ($line_GPRMC, $whats_leftover_GPRMC, $checksum_GPRMC);
  my ($time, $junk, $day, $month, $year, $deg, $min);
  my ($utc_time_gprmc, $status, $lat, $lat_dir, $long, $long_dir, $spd, $track, $date, $checksum) = 0;
  my ($mag_var, $mag_var_dir, $gpsmode, $utc_time_gpgga) = 0;
  my ($alt);

  # Fills data_array with matches to format
  # matches $GPGGA followed by any number of characters followed by CR/LF
  @data_array = ($input_data =~ m/\$GPGGA.+\x0D\x0A/gio);
  $whats_leftover_GPGGA = $'; # Perl special variable that holds everything AFTER the last match
  $line_GPGGA = pop(@data_array); # Perl special variable that holds the last matched data pattern

  # fills data_array with matches to format
  # matches $GPRMC followed by any number of characters followed by CR/LF
  @data_array = ($input_data =~ m/\$GPRMC.+\x0D\x0A/goi);
  $whats_leftover_GPRMC = $'; # Perl special variable that holds everything AFTER the last match
  $line_GPRMC = pop(@data_array); # Get last matched patter

  # Make sure that BOTH GPRMC and GPGGA words have been received before decoding data
  # Return full line and do not decode if both words are not part of frame.

  $checksum = 0;

  # both GPRMC and GPGGA frame must be received and have the same time

  # Decode GPRMC data frame
  if (defined($line_GPRMC)) {
  
    $checksum += calc_nmea_checksum($line_GPRMC);
    ($junk, $utc_time_gprmc, $status, $lat, $lat_dir, $long, $long_dir, $spd, $track, $date
      , $mag_var, $mag_var_dir, $gpsmode) = split(/,/ , $line_GPRMC);

    # Convert data to default units
    ($day, $month, $year) = unpack('A2 A2 A2', $date);
    $date = $day . '/' . $month . '/' . ($year+2000);
    $utc_time_gprmc = sprintf('%02.0f:%02.0f:%02.0f', unpack('A2 A2 A2', $utc_time_gprmc));
    ($deg, $min) = unpack('A2 A20', $lat);
    $lat = $deg + $min/60;
    ($deg, $min) = unpack('A3 A20', $long);
    $long = $deg + $min/60;
    $spd = $spd * 0.5144444; # m/s

    # Save data into global data hash table
    # Include ALL available data, even if you do not intend to use it at this time
    # Use unquoted names ( date instead of 'data' or "date" ) as it is much faster.
    $self->{data}{date} = $date;
    $self->{data}{utc_time} = $utc_time_gprmc;
    $self->{data}{lat} = $lat;
    $self->{data}{lat_dir} = $lat_dir;
    $self->{data}{long} = $long;
    $self->{data}{long_dir} = $long_dir;
    $self->{data}{spd} = $spd;
    $self->{data}{track} = $track;
  }
  else {
    return;
  }

  # Decode GPGGA data frame
  if (defined($line_GPGGA)) {
    # Decode GPRMC line of GPS data frame
    $checksum += calc_nmea_checksum($line_GPGGA);
    ($junk, $utc_time_gpgga, $junk, $junk, $junk, $junk, $junk
      , $junk, $junk, $alt) = split(/,/ , $line_GPGGA); # unused data is not converted

    $self->{data}{alt} = $alt;
  }
  else {
    # no match found, return ALL data
    return; # ($input_data);
  }

  $self->{data}{checksum} = $checksum;


#  if (length($whats_leftover_GPGGA) < length($whats_leftover_GPRMC)) {
#    return($whats_leftover_GPGGA);
#  }

  $self->{input_data} = $whats_leftover_GPRMC;
  return;
  
  # Include explination of format
  # $GPRMC Output Sentence: example
  # $GPRMC,180432,A,4027.027912,N,08704.857070,W,000.04,181.9,131000,1.8,W,D*25
  # Field  Value    Meaning
  # 1  180432     UTC of position fix in hhmmss format (18 hours, 4 minutes and 32 seconds)
  # 2  A        Status (A - data is valid, V - warning)
  # 3  4027.027912  Geographic latitude in ddmm.mmmmmm format (40 degrees and 27.027912 minutes)
  # 4  N        Direction of latitude (N - North, S - South)
  # 5  08704.857070 Geographic longitude in dddmm.mmmmmm format (87 degrees and 4.85707 minutes)
  # 6  W        Direction of longitude (E - East, W - West)
  # 7  000.04     Speed over ground (0.04 knots)
  # 8  181.9      Track made good (heading) (181.9º)
  # 9  131000     Date in ddmmyy format (October 13, 2000)
  # 10  1.8       Magnetic variation (1.8º)
  # 11  W        Direction of magnetic variation (E - East, W - West)
  # 12  D        Mode indication (A - autonomous, D - differential, N - data not valid)
}

sub set_default_values {
  (
   { simfile=>'', baudrate=>'4800'},
  );
}

sub simulate {
  # Simulate NMEA data
  my ($com_data) = '';
  $com_data .= "\$GPRMC,180432,A,4124.8963,N,08704.857070,W,000.04,181.9,131000,1.8,W,D*25\x0D\x0A";
  $com_data .= "\$GPGGA,180432,4124.8963,N,08151.6838,W,1,05,1.5,280.2,M,-34.0,M,,,*75\x0D\x0A";
  return($com_data);
}


sub from_file {
   my ($self, $filename) = @_;
   my ($filedata);
   
   if (!defined($filename) || ($filename eq '')) {
      return;
   }
   
   my $bytes_per_sec = 500; # How fast to read data from file
   
   # Number of bytes to read each scan
   my $bytes_per_scan = $bytes_per_sec / $main::config_data{general}{scan_data_rate};
   
   if (!defined($self->{simfilehandle})) {
      open($self->{simfilehandle}, "<$filename") or return;
   }
   
   if (sysread($self->{simfilehandle}, $filedata, $bytes_per_scan)) {
      return($filedata);
   }
   else {
      close($self->{simfilehandle});
      undef($self->{simfilehandle});
   }
}

# The following line MUST be included and should be the last line in the file
# It returns the name of the package that was loaded as the return value
# from the 'require' statement that loads this module
__PACKAGE__;
