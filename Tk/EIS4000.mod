# Module to read Grand Rapids Research EIS 4000 and EIS 6000
# Engine Monitors
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
# Tested using EIS 4000
#
#
# Release / Change History
# Still in alpha test stage

use warnings;
use strict;

package EIS_4000;
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
# names must match exactly field names in main::data hash further below.
my @fields = (
   'eng_rpm', 'cht_1', 'cht_2', 'cht_3', 'cht_4', 'cht_5', 'cht_6'
   , 'egt_1', 'egt_2', 'egt_3', 'egt_4', 'egt_5', 'egt_6', 'airspeed', 'alt'
   , 'voltage', 'fuel_flow', 'unit_temp', 'carb', 'vert_spd', 'oat', 'oil_temp'
   , 'oil_press', 'coolant_temp', 'hour_meter', 'fuel_totalizer', 'flight_time'
   , 'time_till_empty', 'baro', 'mag_heading',
   , 'DAUX1', 'DAUX2', 'AUX1', 'AUX2', 'AUX3', 'AUX4', 'checksum',
);

my %units = (
   eng_rpm => 'rpm',
   cht_1 => 'Deg C',
   cht_2 => 'Deg C',
   cht_3 => 'Deg C',
   cht_4 => 'Deg C',
   cht_5 => 'Deg C',
   cht_6 => 'Deg C',
   egt_1 => 'Deg C',
   egt_2 => 'Deg C',
   egt_3 => 'Deg C',
   egt_4 => 'Deg C',
   egt_5 => 'Deg C',
   egt_6 => 'Deg C',
   airspeed => 'Knots',
   alt => 'Feet',
   voltage => 'Volts',
   fuel_flow => 'GPH',
   unit_temp => 'Deg C',
   carb => 'Deg C',
   vert_spd => 'Ft / min',
   oat => 'Deg C',
   oil_temp => 'Deg C',
   oil_press => 'PSIG',
   coolant_temp => 'Deg C',
   hour_meter => 'HH:MM:SS',
   fuel_totalizer => 'Gals',
   flight_time => 'HH:MM:SS',
   time_till_empty => 'HH:MM:SS',
   baro => 'Inch HG',
   mag_heading => 'Deg',
   DAUX1 => '',
   DAUX2 => '',
   AUX1 => 'in HG',
   AUX2 => '',
   AUX3 => '',
   AUX4 => '',
   checksum => '',
);

my %chan_label = (
   eng_rpm => 'Engine RPM',
   cht_1 => 'CHT 1',
   cht_2 => 'CHT 2',
   cht_3 => 'CHT 3',
   cht_4 => 'CHT 4',
   cht_5 => 'CHT 5',
   cht_6 => 'CHT 6',
   egt_1 => 'EGT 1',
   egt_2 => 'EGT 2',
   egt_3 => 'EGT 3',
   egt_4 => 'EGT 4',
   egt_5 => 'EGT 5',
   egt_6 => 'EGT 6',
   airspeed => 'Airspeed',
   alt => 'Altitude',
   voltage => 'Ess Bus Voltage',
   fuel_flow => 'Fuel Flow',
   unit_temp => 'Unit Temp',
   carb => 'Carb Temp',
   vert_spd => 'Vertical Spd',
   oat => 'OAT',
   oil_temp => 'Oil Temp',
   oil_press => 'Oil Pressure',
   coolant_temp => 'Coolant Temp',
   hour_meter => 'Hour Meter',
   fuel_totalizer => 'Fuel Totalizer',
   flight_time => 'Flight Time',
   time_till_empty => 'Time Till Empty',
   baro => 'Barometer',
   mag_heading => 'Mag Heading',
   DAUX1 => 'DAUX1',
   DAUX2 => 'DAUX2',
   AUX1 => 'MP',
   AUX2 => 'AUX2',
   AUX3 => 'AUX3',
   AUX4 => 'AUX4',
   checksum => 'Checksum',
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
   # Win32 work around for this speed missing from list
   # of valid baudrates
   $porthandle->{_L_BAUD}{115200} = 115200;

   # Setup serial port
   $porthandle->baudrate(9600);
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

sub calc_EIS4000_checksum {
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
   my ($self, $new_data) = @_;
   if (!defined($new_data)) {
      return;
   }
   my ($input_data);
   my ($line, @data_array, $whats_leftover);
   
   $input_data = $self->{old_data} . $new_data;

   # Variables specific to the EIS-4000/6000
   my ($TACH, $CHT1, $CHT2, $CHT3, $CHT4, $CHT5, $CHT6,
     $EGT1, $EGT2, $EGT3, $EGT4, $EGT5, $EGT6, $DAUX1, 
     $DAUX2, $ASPD, $ALT, $VOLT, $FUEL_FLOW, $UNIT_TEMP,
     $CARB, $ROCSGN, $OAT, $OILT, $OILP, $AUX1, $AUX2, 
     $AUX3, $AUX4, $COOL, $ETI, $QTY, $HRS, $MIN, $SEC,
     $ENDHRS, $ENDMIN, $BARO, $MAGHD, $SPARE, $CHKSUM, $checksum) = 0;

   # fills data_array with matches to format
   # matches 3 byte header followed by any number 70 bytes of data
   @data_array = ($input_data =~ m/\xfe\xff\xfe[\x00-\xff]{70}/goi);
   $whats_leftover = $'; # Perl special variable that holds everything AFTER the last match
   $line = pop(@data_array); # Get last matched patten

   # Decode data frame
   if (defined($line)) {
#      $checksum = calc_EIS4000_checksum($line);
      ($TACH, $CHT1, $CHT2, $CHT3, $CHT4, $CHT5, $CHT6,
         $EGT1, $EGT2, $EGT3, $EGT4, $EGT5, $EGT6, $DAUX1, 
         $DAUX2, $ASPD, $ALT, $VOLT, $FUEL_FLOW, $UNIT_TEMP,
         $CARB, $ROCSGN, $OAT, $OILT, $OILP, $AUX1, $AUX2, 
         $AUX3, $AUX4, $COOL, $ETI, $QTY, $HRS, $MIN, $SEC,
         $ENDHRS, $ENDMIN, $BARO, $MAGHD, $SPARE, $CHKSUM) = 
         unpack('x3 n19 C c3 n C n7 C5 nn CC', $line);

      # Convert data to default units and save into global data hash
      $self->{data}{eng_rpm} = $TACH;
      $self->{data}{cht_1} = $CHT1;
      $self->{data}{cht_2} = $CHT2;
      $self->{data}{cht_3} = $CHT3;
      $self->{data}{cht_4} = $CHT4;
      $self->{data}{cht_5} = $CHT5;
      $self->{data}{cht_6} = $CHT6;
      $self->{data}{egt_1} = $EGT1;
      $self->{data}{egt_2} = $EGT2;
      $self->{data}{egt_3} = $EGT3;
      $self->{data}{egt_4} = $EGT4;
      $self->{data}{egt_5} = $EGT5;
      $self->{data}{egt_6} = $EGT6;
      $self->{data}{DAUX1} = $DAUX1;
      $self->{data}{DAUX2} = $DAUX2;
      $self->{data}{airspeed} = $ASPD;
      $self->{data}{alt} = $ALT;
      $self->{data}{voltage} = $VOLT / 10;
      $self->{data}{fuel_flow} = $FUEL_FLOW / 10;
      $self->{data}{unit_temp} = $UNIT_TEMP;
      $self->{data}{carb} = $CARB;
      $self->{data}{vert_spd} = $ROCSGN * 100;
      $self->{data}{oat} = $OAT;
      $self->{data}{oil_temp} = $OILT;
      $self->{data}{oil_press} = $OILP;
      $self->{data}{AUX1} = $AUX1 / 10;
      $self->{data}{AUX2} = $AUX2;
      $self->{data}{AUX3} = $AUX3;
      $self->{data}{AUX4} = $AUX4;
      $self->{data}{coolant_temp} = $COOL;
      $self->{data}{hour_meter} = $ETI / 10;
      $self->{data}{fuel_totalizer} = $QTY;
      $self->{data}{flight_time} = "$HRS:$MIN:$SEC";
      $self->{data}{time_till_empty} = "$ENDHRS:$ENDMIN:00";
      $self->{data}{baro} = $BARO / 100;
      $self->{data}{mag_heading} = $MAGHD / 100;

      # Save any leftover data for use during the next scan
      $self->{old_data} = $whats_leftover; 
   }
   else {
      # No data was decoded
      # Append incoming data to previously recieved data for use next scan
      $self->{old_data} .= $new_data; 
   }
   
   # Need to include information about data format
}

sub set_default_values {
  (
   { simfile=>''},
  );
}

sub simulate {
   my (@dataarray);
   my ($frame, $i);
   
   for ($i = 0 ; $i<=43 ; $i++) {
      push(@dataarray, $i);
   }
   $dataarray[0] = 254;
   $dataarray[1] = 255;
   $dataarray[2] = 254;
   $dataarray[23] = -23;
   $dataarray[24] = -24;
   $dataarray[25] = -25;

   # EIS 4000 data
   $frame = pack('C3 n19 C c3 n C n7 C5 nn CC', @dataarray);
   
   return($frame);
}

sub from_file {
   my ($self, $filename) = @_;
   my ($filedata);

return(simulate());
   
   if (!defined($filename) || ($filename eq '')) {
      return;
   }
   
   my $bytes_per_sec = 150; # How fast to read data from file
   
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
