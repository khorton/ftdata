# Module to read data from Garmin GNS-430 Aircraft GPS unit
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

package GNS430;
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
my @fields = ('alt', 'lat', 'long', 'track', 'spd'
   , 'dist_wpt', 'xtrack_err', 'des_track', 'wpt_id', 'wpt_brg'
   , 'mag_var', 'nav_valid', 'warn_stat', 'dist_dest');

my %chan_label = (
   'alt'        => 'Altitude',
   'lat'        => 'Latitude',
   'long'       => 'longitude',
   'track'      => 'Track',
   'spd'        => 'Speed',
   'xtrack_err' => 'Cross Track Err',
   'dist_wpt'   => 'Distance to Waypoint',
   'des_track'  => 'Desired Track',
   'wpt_id'     => 'Waypoint ID',
   'wpt_brg'    => 'Waypoint Bearing',
   'mag_var'    => 'Magnetic Variation',
   'nav_valid'  => 'Nav Valid Flag',
   'warn_stat'  => 'Warning Status',
   'dist_dest'  => 'Destination Distance',
);

my %units = (
   'alt'        => 'ft',
   'lat'        => 'Degrees',
   'long'       => 'Degrees',
   'track'      => 'Degrees',
   'spd'        => 'knots',
   'xtrack_err' => 'Miles',
   'dist_wpt'   => 'Miles',
   'des_track'  => 'Degrees',
   'wpt_id'     => '',
   'wpt_brg'    => 'Degrees',
   'mag_var'    => 'Degrees',
   'nav_valid'  => '',
   'warn_stat'  => '',
   'dist_dest'  => 'nm',
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

sub decode_data {
   my ($self, $new_data) = @_;
   if (!defined($new_data)) {
      return;
   }
   my ($input_data);
   my ($line, @data_array, $whats_leftover);
   
   $input_data = $self->{old_data} . $new_data;

   # Variables specific to the GNS-430
   my ($junk, $alt, $lat, $long, $track, $spd, $dist_wpt, $xtrack_dir, $xtrack_dist);
   my ($des_track, $wpt_id, $wpt_brg, $mag_var, $nav_valid, $warn_stat, $dist_dest);
   my ($xtrack_err, $ew, $dir, $deg, $min);
   
   # Fills @data_array with all matches
   $line = $input_data;
   @data_array = ($input_data =~ m/\x02.+?\x03/sgo);
   # Searches for text with hex(02) at beginning and hex(03) at end
   # marking the beginning and end of a frame of data
   $whats_leftover = $'; # Perl special variable that holds everything AFTER the last match
   $line = pop(@data_array); 

   if (defined($line)) {
      ($alt) =  ($line =~ m/z.{5}/sgo);
      ($junk, $alt) = unpack('A1 A5', $alt);
      
      ($lat) =  ($line =~ m/A.{9}/sgo);
      ($junk, $dir, $deg, $min) = unpack('A1 A1 x A3 A4', $lat);
      $lat = $deg + $min/6000;

      ($long) =  ($line =~ m/B.{10}/sgo);
      ($junk, $dir, $deg, $min) = unpack('A1 A1 x A4 A4', $long);
      $long = $deg + $min/6000;

      ($track) =  ($line =~ m/C.{3}/sgo);
      ($junk, $track) = unpack('A1 A3', $track);

      ($spd) =  ($line =~ m/D.{3}/sgo);
      ($junk, $spd) = unpack('A1 A3', $spd);

      ($dist_wpt) =  ($line =~ m/E.{5}/sgo);
      ($junk, $dist_wpt) = unpack('A1 A5', $dist_wpt);
      if ($dist_wpt ne '-----') {
         $dist_wpt /= 10;
      }

      ($xtrack_dist) =  ($line =~ m/G.{5}/sgo);
      ($junk, $xtrack_dir, $xtrack_dist) = unpack('A1 A1 A4', $xtrack_dist);
      if ($xtrack_dist ne '----') {
         $xtrack_dist /= 100;
         $xtrack_err = $xtrack_dir . $xtrack_dist;
      }

      ($des_track) =  ($line =~ m/I.{4}/sgo);
      ($junk, $des_track) = unpack('A1 A4', $des_track);
      if ($des_track ne '----') {
         $des_track /= 10;
      }

      ($wpt_id) =  ($line =~ m/K.{5}/sgo);
      ($junk, $wpt_id) = unpack('A1 A5', $wpt_id);

      ($wpt_brg) =  ($line =~ m/L.{4}/sgo);
      ($junk, $wpt_brg) = unpack('A1 A4', $wpt_brg);
      if ($wpt_brg ne '----') {
         $wpt_brg /= 10;
      }

      ($mag_var) =  ($line =~ m/Q.{4}/sgo);
      ($junk, $ew, $mag_var) = unpack('A1 A1 A3', $mag_var);
      if ($mag_var ne '---') {
         $mag_var /= 10;
      }
      $mag_var = $ew . ' ' . $mag_var;

      ($nav_valid) =  ($line =~ m/S.{5}/sgo);
      ($junk, $junk, $nav_valid) = unpack('A1 A4 A1', $nav_valid);
      if ($nav_valid eq 'N') {
         $nav_valid = 'Not Valid';
      }
      else {
         $nav_valid = 'Valid';
      }

      ($warn_stat) =  ($line =~ m/T.{9}/sgo);
      ($junk, $warn_stat) = unpack('A1 A9', $warn_stat);

      ($dist_dest) =  ($line =~ m/l.{6}/sgo);
      ($junk, $dist_dest) = unpack('A1 A6', $dist_dest);
      if ($dist_dest ne '------') {
         $dist_dest /= 10;
      }

      # Save data into global data hash table
      # Include ALL available data, even if you do not intend to use it at this time
      # The parameters to be saved will come from this list
      # Use unquoted names ( time instead of 'time' or "time" ) as it is much faster.
      $self->{data}{alt} = $alt;
      $self->{data}{lat} = $lat;
      $self->{data}{long} = $long;
      $self->{data}{track} = $track;
      $self->{data}{spd} = $spd;
      $self->{data}{dist_wpt} = $dist_wpt;
      $self->{data}{xtrack_err} = $xtrack_err;
      $self->{data}{des_track} = $des_track;
      $self->{data}{wpt_id} = $wpt_id;
      $self->{data}{wpt_brg} = $wpt_brg;
      $self->{data}{mag_var} = $mag_var;
      $self->{data}{nav_valid} = $nav_valid;
      $self->{data}{warn_stat} = $warn_stat;
      $self->{data}{dist_dest} = $dist_dest;
   }
   else {
      # no match found, return ALL data
      return;
   }

   # whats left from data stream will be used during next scan
   $self->{input_data} = $whats_leftover; 
   
   # Include format of data stream
   # From the GNS-430 manual dated ??/??/????
}

sub set_default_values {
  (
   { simfile=>''},
  );
}

sub simulate {

}

sub from_file {
   my ($self, $filename) = @_;
   my ($filedata);
   
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
