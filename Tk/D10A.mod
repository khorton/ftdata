# Module to read data from Dynon Avionics EFIS-D10A
#
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
# Tested with ??, firmware ver??
#
#
# Release / Change History
# Still in alpha testing stage
#

use warnings;
use strict;

package D10A;
# package is a unique name for each type of device you want to read
# Multiple devices of the same type can be read from different
# comm ports. This is also the device name that will be referenced
# through out this module and the name which will appear on the device list
# the user selects from

my ($device_name) = __PACKAGE__;

# Add device name to list of available devices
#push(@main::device_list, $device_name);

# Version info will have meaning in the future
my $version = 0.2; # must be numeric
my $date = '23 Oct 2005';

# Detect of Win32 system
my $OS_win = ($^O eq "MSWin32") ? 1 : 0;

# What fields will be recorded and in what order for each device
my @fields = ('time', 'pitch', 'roll', 'yaw', 'spd'
   , 'alt', 'turn_rate', 'g_lat', 'g_vert', 'aoa');

my %chan_label = (
   'time'      => 'Time',
   'pitch'     => 'Pitch',
   'roll'      => 'Roll',
   'yaw'       => 'Yaw',
   'spd'       => 'Speed',
   'alt'       => 'Alt',
   'turn_rate' => 'Turn Rate',
   'g_lat'     => 'G Lateral',
   'g_vert'    => 'G Verticle',
   'aoa'       => 'AOA',
);

my %units = (
   'time'      => 'hh:mm:ss.sss',
   'pitch'     => 'deg',
   'roll'      => 'deg',
   'yaw'       => 'deg',
   'spd'       => 'kt',
   'alt'       => 'ft',
   'turn_rate' => 'deg/s',
   'g_lat'     => 'g',
   'g_vert'    => 'g',
   'aoa'       => '%stall angle',
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
	my $class = shift;
	my $self = {};

	# Load default values
	$self->{device} = $device_name;
	@{$self->{'fields'}} = @fields;
	%{$self->{'units'}} = %units;
	%{$self->{'label'}} = %chan_label;

	$self->{'porttype'} = 'serial';

	%{$self->{'data'}} = ();
   $self->{old_data}	='';
	
	$self->{version} = $version;
	$self->{date} = $date;

	$self->{device_num} = -1;

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

   # Add 115200 to the permitted port speeds.
   # Win32 work around for this speed may be missing from list
   # of valid baudrates on some version of Windows
   # Not sure if this is needed or valid for OS-X or Linux
   $porthandle->{_L_BAUD}{115200} = 115200;

   # Setup serial port
   $porthandle->baudrate(115200);
   $porthandle->databits(8);
   $porthandle->parity('none');
   $porthandle->stopbits(1);
   $porthandle->handshake('none');
   
   $porthandle->write_settings();
   
   # Save reference to serial port
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

sub decode_data {
   my ($self, $new_data) = @_;
   if (!defined($new_data)) {
      return;
   }
   my ($input_data);
   my ($line, @data_array, $whats_leftover);
   
   $input_data = $self->{old_data} . $new_data;

   my ($format);

   my ($hr, $min, $sec, $sec_frac, $pitch, $roll, $yaw, $spd, $alt) = 0;
   my ($turn_rate, $g_lat, $g_vert, $aoa, $status, $product_id, $checksum, $crlf) = 0;

   # Refer to perl's pack and unpack functions for explanation of format
   # Use this method if data is always in the exact same position in the data string
   # 43 characters full frame of data including CR/LF at end of data

   # D10 format, firmware v1.x ???
   # $format = "A2 A2 A2 A2 A4 A5 A3 A4 A5 A4 A3 A3 A2 A2";
   
   # D10A format, firmware v2.x ???
   $format = "A2 A2 A2 A2 A4 A5 A3 A4 A5 A4 A3 A3 A2 A6 A2 A2 A2";

   # Fills data_array with all matches
   # D10 format, firmware v1.x ???
   # @data_array = ($input_data =~ m/[0-9+-]{41}\x0D\x0A/go);
   # searches for any 41 characters followed by CR/LF
   
   # D10A format, firmware v2.x ???
   @data_array = ($input_data =~ m/[0-9A-F+-]{51}\x0D\x0A/go);
   # searches for any 51 characters followed by CR/LF

   $whats_leftover = $'; # Perl special variable that holds everything AFTER the last match
   $line = pop(@data_array); # Perl special variable that holds the last matched data pattern

   if (defined($line)) {
      # D10
      # Decode line of serial data
      #($hr, $min, $sec, $sec_frac, $pitch, $roll, $yaw, $spd, $alt,
      #   $turn_rate, $g_lat, $g_vert, $aoa, $crlf) = unpack($format, $line);
      
      # D10A
      ($hr, $min, $sec, $sec_frac, $pitch, $roll, $yaw, $spd, $alt,
         $turn_rate, $g_lat, $g_vert, $aoa, $status, $product_id, $checksum, $crlf) = unpack($format, $line);

      # Convert data to default units
      $sec = $sec + ($sec_frac/64);
      $pitch = $pitch / 10;
      $roll = $roll / 10;
      $spd = $spd * 0.1943846; # convert to kt
      $alt = $alt * 3.28084; # convert to feet
      $turn_rate = $turn_rate / 10;
      $g_lat = $g_lat / 10;
      $g_vert = $g_vert / 10;

      # Save data into global data hash table
      # Include ALL available data, even if you do not intend to use it at this time
      # The parameters to be saved will come from this list
      # Use unquoted names ( time instead of 'time' or "time" ) as it is much faster.
      $self->{data}{time} = "$hr:$min:$sec";
      $self->{data}{pitch} = $pitch;
      $self->{data}{roll} = $roll;
      $self->{data}{yaw} = $yaw;
      $self->{data}{spd} = $spd;
      $self->{data}{alt} = $alt;
      $self->{data}{turn_rate} = $turn_rate;
      $self->{data}{g_lat} = $g_lat;
      $self->{data}{g_vert} = $g_vert;
      $self->{data}{aoa} = $aoa;

      # Save any leftover data for use during the next scan
      $self->{old_data} = $whats_leftover; 
   }
   else {
      # No data was decoded
      # Append incoming data to previously received data for use next scan
      $self->{old_data} .= $new_data; 
   }
   
   # Include format of data stream
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
   #
   # Start Width Description Notes
   # 1      2    Hour 00 to 23, current hour according to EFIS-D10A's internal clock
   # 3      2    Minute 00 to 59, current minute according to EFIS-D10A's internal clock
   # 5      2    Second 00 to 59, current second according to EFIS-D10A's internal clock
   # 7      2    Fractions 00 to 63, counter for 1/64 second. Data output frequency.
   # 9      1    Pitch Sign '+' or '-' (positive means plane is pitched up)
   # 10     3    Pitch 000 to 900, pitch up or down from level flight in 1/10 degrees (900 = 90 Degs)
   # 13     1    Roll Sign '+' or '-' (positive means plane is banked right)
   # 14     4    Roll 0000 to 1800, roll left or right from level flight in 1/10 degrees (1800 = 180 Degs)
   # 18     3    Yaw 000 to 359 in degrees (000 = North, 090 = East, 180 = South, 270 = West)
   # 21     4    Airspeed 0000 to 9999, airspeed in units of 1/10 m/s (1555 = 155.5 m/s)
   # 25     1    Altitude Sign '+' or '-' (positive means altitude is above sea-level)
   # 26     4    Altitude 0000 to 9999, altitude in units of meters
   # 30     1    Turn Rate Sign '+' or '-' (positive means plane is turning right)
   # 31     3    Turn Rate 000 to 999, 1/10 degrees/second rate of yaw change
   # 34     1    Lateral G's Sign '+' or '-' (positive means plane is experiencing leftward lateral acceleration)
   # 35     2    Lateral G's 00 to 99, lateral G's in units of 1/10 G (99 = 9.9 G's)
   # 37     1    Vertical G's Sign '+' or '-' (positive means plane is experiencing upward vertical acceleration)
   # 38     2    Vertical G's 00 to 99, vertical G's in units of 1/10 G (99 = 9.9 G's)
   # 40     2    Angle of Attack 00 to 99, percentage of stall angle.
   # 42     2    CR/LF Carriage Return, Linefeed = 0x13, 0x10
}

sub set_default_values {
  (
   { simfile=>''},
  );
}

sub simulate {
   # Simulate D10A data
   my ($rand2) = sprintf("%04d", rand(10000));
   return ("00071717+109+00092450000+" . $rand2 . "+007-00+1099\x0D\x0A");
}

sub from_file {
   my ($self, $filename) = @_;
   my ($filedata);
   
   if (!defined($filename) || ($filename eq '')) {
      return;
   }
   
   my $bytes_per_sec = 2753.92; # How fast to read data from file
   
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
