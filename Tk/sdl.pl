#!/usr/bin/perl
#
# sdl.pl
#
# Acquires data from multiple sources
# Displays and saves data to file
# Perl script to record serial data various instruments
# High resolution computer time is appended to each data record
# to facilitate time sync with multiple data sources.
#
# Copyright (c) 2005, Michael Ketterman
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Release status:
# This software is in the early stages of development and may be broken.
#
# Default units are: 'm', 'm/s', 'degC', 'ddd.dddddd' for position, 'ddd.ddd' for angles/direction
#
# Inspired by Kevin Horton and his RV-8 project

use warnings;
use strict;

my ($version) = '0.2 Development';
my ($verdate) = '23 Oct 2005';

use Time::HiRes qw( time sleep gettimeofday );
use POSIX;
use Tk;
use Tk::BrowseEntry;
use Tk::Label;
use Tk::Dialog;
use Tk::Menu;
use Tk::Pane;
use Tk::NoteBook;
use Tk::DialogBox;
use Tk::Checkbutton;
use Tk::Font;

# Note
# Requires that either Win32::SerialPort (for a Windows machine)
# or Device::SerialPort (for a Linux or Mac OS-X machine)
# be installed.
# Win32::SerialPort is not part of the standard Activestate distribution
# of perl for Win32

# If using ActiveState Perl for Win32, perl v5.6 or 5.8
# win32::Serialport can be installed with the following command
# ppm install http://www.bribes.org/perl/ppm/Win32-SerialPort.ppd
#

# Detect Operating system and load appropiate serial port module
use vars qw( $OS_win );
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

# Global variables
my (%devices); # Hash of ALL devices that are defined and all available data
my (@device_list) = (); # List of active devices, could have multiple entries for each device type
my (@device_type);  # List of all available devices, one entry per device type
my (@device_ref) = ();

# Hash containing all data, ONE scan of the most recent data for all devices
# Format for accessig data is $data{device name}{data field};
my (%data) = ();
my (%com_data) = (); # Place to
my (@coms) = (); # List of all com ports available
my (@com_list) = (); #list of all com ports used
my (@com_handle);
my ($mw, $frame, $scan_state, %timed_events, $start_btn, $stop_btn);
my @display = (); # $display[dev#][chan#] Variable that the displays are mapped to
my @dispitem = (); # $dispitem[row][col] display item reference variable, used by TK grid placement
my ($config_file) = 'sdl.ini';
my ($logfilehandle);

# Include all global variables that you want other modules to access
our (%devices, @device_list, %data, %config_data);

# Be sure to execute this AFTER all global variables have been defined

# Load all ./*.mod files
load_modules();

# Load config data AFTER loading device modules
%config_data = read_config_file($config_file);

@coms = detect_commports();
@device_type = @{$config_data{modules}{active_list}};
@com_list = @{$config_data{modules}{comports}};
make_gui();

MainLoop;

exit;

sub scan_data {
   my ($device);
   my ($dev_num);
   my ($num_devices) = $config_data{modules}{number};

   # Schedule next call to this function
   $timed_events{scan_data}->after(1000/$config_data{general}{scan_data_rate}, \&scan_data);

   read_comports();

   # Send comport data to selected device decoding subroutine
   for ($dev_num = 0; $dev_num < $num_devices; $dev_num++) {
      $device = $device_type[$dev_num];
      if (($com_list[$dev_num] ne 'None') & ($device ne 'None')) {
#         $com_data{$com_list[$dev_num]} = &{$devices{$device}{'sub'}}($dev_num, $com_data{$com_list[$dev_num]});
      }
   }
}

sub start_scan {
   my ($dev_num);
   my ($num_devices) = $config_data{modules}{number};
   my ($error, $com) = 0;
   my (%temp) = ();

   # Do nothing if already scanning
   if ($scan_state) { return; }

   # Check to ensure that each com port is only selected once
   foreach $com (@com_list) {
      if ((!defined($temp{$com})) or ($com eq 'None')) {
         $temp{$com} = 1;
      }
      else {
         $mw->Dialog(
            -text => "Com port '$com' used more than once\nCannot start scanning",
            -buttons => ['OK'],
         ) ->Show;
         $error = 1;
      }
   }
   if ($error) {return};

   @com_handle = (); # Clear previous handle data

   # Open all selected com ports
   for ($dev_num = 0; $dev_num < $num_devices; $dev_num++) {
      if ((!defined($device_ref[$dev_num])) || ($com_list[$dev_num] eq 'None') || ($device_ref[$dev_num] eq 'None')) {
         next;
      }
      
      $device_ref[$dev_num]->open_comm_port($com_list[$dev_num]);

      if (!defined($device_ref[$dev_num]->{porthandle})) {
         # Error opening serial port.
         # close any opened serial ports
         foreach $com (@device_ref) {
            $com->close_comm_port();
         }
         return;
      }
   }

   # Check to ensure that at least 1 serial port has been opened
   $error = 1;
   foreach $com (@device_ref) {
      if (defined($com->{porthandle})) {
         $error = 0;
      }
   }
   if ($error) {
      $mw->Dialog(
         -text => "No serial ports selected\nScanning not started",
         -buttons => ['OK'],
      ) ->Show;
      return();
   }

   open_log_file();

   $start_btn->configure(-state =>'disabled');
   $stop_btn->configure(-state =>'active');

   $scan_state = 1;

   #Check for new data every x ms
   $timed_events{scan_data}=$mw->Label;
   scan_data(); # Event timing is defined in function

   # Update displayed data every x ms
   # Updating the display more that 10 times per sec (100 ms) is not
   # reccomended as it makes it difficult to actually see the changing number.
   $timed_events{update_display}=$mw->Label;
   update_display(); # Event timing is defined in function

   # Call and set log data file rate
   if (defined($logfilehandle)) {
      $timed_events{save_log_data}=$mw->Label;
      save_log_data(); # Event timing is defined in function
   }
}

sub open_log_file {
   my ($dev_num);
   my ($num_devices) = $config_data{modules}{number};
   my ($filename, @list, $item);
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time());

   my $types = [ ['Comma Seperated Variable', '.csv'],
                 ['Comma Seperated Variable', '.csv']
               ];

   $mon++;
   if ($year > 100) { $year -= 100; };

   # Get filename to save data to
   $filename = sprintf("%02.0f%02.0f%02.0f%02.0f%02.0f", $year, $mon, $mday, $hour, $min);
   $filename = $mw->getSaveFile(
      -initialfile => $filename,
      -title => 'Save Output Data',
      -filetypes => $types,
      -defaultextension => '.csv',
   );

   if (defined($filename)) {
      #$logfilehandle = \*STDOUT;
      open(LOGFILE, ">$filename");
      if (defined(\*LOGFILE)) {
         $logfilehandle = \*LOGFILE;
      }
      else {
         $mw->Dialog(
            -text => "No log file will be saved\nCould not open file\n$filename",
            -buttons => ['OK'],
         ) ->Show;
      }
   }
   else {
      undef($logfilehandle);
   }

   # Print log file header information
   if (defined($logfilehandle)) {
      # Print field name descriptions
      print $logfilehandle "\"Time\"";
      for ($dev_num = 0; $dev_num < $num_devices; $dev_num++) {
         if ($device_type[$dev_num] ne 'None') {
            @list = @{$devices{$device_type[$dev_num]}{'fields'}};
            foreach $item (@list) {
               print $logfilehandle ",\"$device_type[$dev_num] $item\"";
            }
         }
      }
      print $logfilehandle "\n";
      print $logfilehandle "\"MM/DD/YY hh:mm:ss.000\"";
      for ($dev_num = 0; $dev_num < $num_devices; $dev_num++) {
         if ($device_type[$dev_num] ne 'None') {
            @list = @{$devices{$device_type[$dev_num]}{'fields'}};
            foreach $item (@list) {
               if (defined($devices{$device_type[$dev_num]}{units}{$item})) {
                  print $logfilehandle ",\"$devices{$device_type[$dev_num]}{units}{$item}\"";
               }
               else {
                  print $logfilehandle ",\"\"";
               }
            }
         }
      }
      print $logfilehandle "\n";
   }
}

sub stop_scan {
   my ($dev_num, $com);
   my ($num_devices) = $config_data{modules}{number};
   my ($events);

   # Do nothing of not scanning
   if (!$scan_state) { return; }

   $scan_state = 0;
   # Destroy ALL timed events
   foreach $events (keys(%timed_events)) {
      if(defined($timed_events{$events})) {
         $timed_events{$events}->destroy;
         undef($timed_events{$events});
      }
   }

   # Close log file
   if (defined($logfilehandle)) {
      close($logfilehandle);
   }

   $start_btn->configure(-state =>'active');
   $stop_btn->configure(-state =>'disabled');

   # Close all com ports
   foreach $com (@device_ref) {
      $com->close_comm_port();
   }
}

sub read_comports {
   my ($i, $dev_num, $device);
   my ($num_devices) = $config_data{modules}{number};
   my ($com_dat);

   # Simulated serial data
   if ($config_data{general}{simulate} == 1) {
      for ($dev_num = 0; $dev_num < $num_devices; $dev_num++) {
         $device = $device_type[$dev_num];
         if (defined($com_list[$dev_num]) && (defined($device_ref[$dev_num]))
               && ($device ne 'None') && ($com_list[$dev_num] ne 'None')) {
            $com_dat = $device_ref[$dev_num]->from_file($config_data{$device}{simfile});
            $device_ref[$dev_num]->decode_data($com_dat);
         }
      }
   }
   # Read real serial data
   else {
      for ($dev_num = 0; $dev_num < $num_devices; $dev_num++) {
         # Read serial port data, only if handle is "defined"
         if (defined($device_ref[$dev_num])) {
            $com_dat = $device_ref[$dev_num]->read_comm_port();
            $device_ref[$dev_num]->decode_data($com_dat);
#            $com_data{$com_list[$dev_num]} .= $com_handle[$dev_num]->input() if ($com_list[$dev_num] ne 'None');
         }
      }
   }
}

sub save_log_data {
   # Save data from all devices to file
   if(!defined($logfilehandle))
   { return; }

   my @chan_list = ();
   my ($device, $chan, @timearray, $time);
   my ($sec,$min,$hour,$mday,$mon,$year, $secfrac, $systime);

   my ($dev_num);
   my ($num_devices) = $config_data{modules}{number};

   # Schedule next call to this function
   $timed_events{save_log_data}->after(1000/$config_data{general}{save_log_data_rate}, \&save_log_data);

   # Get time, including milliseconds
   $time = gettimeofday();
   ($sec,$min,$hour,$mday,$mon,$year) = localtime($time);
   $secfrac = $time - floor($time);
   $mday++;
   $year = $year + 1900;
   $sec = $sec + $secfrac;
   $systime = sprintf ("%02.0f/%02.0f/%02.0f %02.0f:%02.0f:%02.3f", $mon,$mday,$year,$hour,$min,$sec);

   # Time data saved to log file
   print $logfilehandle $systime;

   for ($dev_num = 0; $dev_num < $num_devices; $dev_num++) {
      if ($device_type[$dev_num] ne 'None') {
         @chan_list = @{$device_ref[$dev_num]->{'fields'}};
         foreach $chan (@chan_list) {
            if (defined($device_ref[$dev_num]->{data}{$chan})) {
               print $logfilehandle ', ' . $device_ref[$dev_num]->{data}{$chan};
            }
            else {
               print $logfilehandle ', NaN';
            }
         }
      }
   }
   print $logfilehandle "\n";
}

sub load_modules {
   my ($module, @module_list, @files, $device_name);
   my ($num_devices) = $config_data{modules}{number};

   # Searches the current directory for all *.mod file
   opendir(DIR, ".");
   @module_list = <./*.mod>;
   closedir(DIR);

   foreach $module (@module_list) {
      $device_name = require $module ;
      
      push(@device_list, $device_name);
      $devices{$device_name} = $device_name->new();
            
      if ($devices{$device_name}->{version} < 0.2) {
        print "Module '$device_name' is designed for program version ";
        print $devices{$device_name}->{version} . "\n";
        print "Minimum module version for this program is 0.2\n";
      }
   }
}

sub make_gui {

   my ($row, $col);
   my ($dev_num, @dev_select, @com_select);
   my ($num_devices) = $config_data{modules}{number};
   # Mainwindow: sizex/y, positionx/y

   $mw = MainWindow->new;

   $mw->geometry($config_data{window}{width} . 'x'
      . $config_data{window}{height}
      . '+' . $config_data{window}{xpos}
      . '+' . $config_data{window}{ypos});

   $mw->title("SDL v$version, $verdate");

   create_menubar();

   $frame = $mw->Scrolled('Pane',
      -scrollbars => 'osoe',
      -sticky => 'nw',
      -gridded => 'y',
   );
   $frame->Frame;
   $frame->pack(-expand => 1, -fill => 'both');

   for ($dev_num = 0; $dev_num < $num_devices ; $dev_num++) {
      $dev_select[$dev_num] = $frame->BrowseEntry(
         -textvariable => \$device_type[$dev_num],
         -options      => \@device_list,
         -command      => [sub {disp_chanlist();}],
         -width        => 12,
      );
      $dev_select[$dev_num]->insert(0, 'None'); # Place 'None' at beginning of list
      $com_select[$dev_num] = $frame->BrowseEntry(
         -textvariable => \$com_list[$dev_num],
         -options      => \@coms,
         -state        => 'readonly',
         -width        => 12,
      );
      $com_select[$dev_num]->insert(0, 'None'); # Place 'None' at beginning of list
   }

   # Setup defaults from config file
   foreach $dev_num (keys(%{$config_data{module_list}})) {
   }
   foreach $dev_num (keys(%{$config_data{comports}})) {
      $com_list[$dev_num] = $config_data{comports}{$dev_num};
   }
   disp_chanlist();

   $row = 1;
   $col = 1;

   $start_btn = $frame->Button(
      -text    => 'Start Scan (F5)',
      -command => \&start_scan,
      -state   => 'active',
   )->grid(-row => $row, -column => $col);

   $col++;

   $stop_btn = $frame->Button(
      -text    => 'Stop Scan(F7)',
      -command => \&stop_scan,
      -state   => 'disabled',
   )->grid(-row => $row, -column => $col);

   $row++;

   $col = 1;

   for ($dev_num = 0; $dev_num < $num_devices ; $dev_num++) {
      $frame->Label(-text => 'Device')->grid(-row => $row, -column => $col);
      $dev_select[$dev_num]->grid(-row => $row + 1, -column => $col);

      $col++;
      $frame->Label(-text => 'Serial Port')->grid(-row => $row, -column => $col);
      $com_select[$dev_num]->grid(-row => $row + 1, -column => $col);

      $col++;
   }

   # Capture keystroke events
   $mw->bind('<KeyPress>' => \&print_keysym);
}
sub create_menubar {

   my $window = $mw;

   my $menubar = $window->Menu(-tearoff => 0);
   my $file_menu = $menubar->cascade(-label => "~File");

   $file_menu->command(-label => "Setup", -command => sub {user_config();});
   $file_menu->command(-label => "Save Setup", -command => sub {save_config_file();});
   $file_menu->separator;
   $file_menu->command(-label => "~Quit",    -command => [$window => 'destroy'] );

   $window->configure(-menu => $menubar);
}

sub print_keysym {
    my($widget) = @_;
    my $e = $widget->XEvent;    # get event object
    my($keysym_text, $keysym_decimal) = ($e->K, $e->N);
    if ($keysym_text eq 'F5') {
       start_scan();
    }
    elsif ($keysym_text eq 'F7') {
       stop_scan();
    }
    return;
}

sub disp_chanlist {
   my ($dev_num);
   my ($num_devices) = $config_data{modules}{number};

   my ($col, $row, $device_name);
   my ($channel, $junk);
   my (@chan_list, $chan_num);

   my ($start_row) = 4;
   my ($start_col) = 1;

   my @font = [ -size => $config_data{general}{font_size}];

   $col = $start_col;
   # Remove ALL device display items and Tk references
   for ($col = 1; $col <= ($num_devices*2); $col++) {
      $row = $start_row;
      while (Exists($dispitem[$row][$col])) {
         $dispitem[$row][$col]->gridForget(); # Remove from display
         $dispitem[$row][$col]->destroy; # Remove all Tk references
         $row++;
      }
   }

   # Create new display items (channel labels and data display items)
   $col = $start_col;
   for ($dev_num = 0; $dev_num < $num_devices ; $dev_num++) {
      $row = $start_row;
      $device_name = $device_type[$dev_num];
      if (!defined($device_name) or !exists($devices{$device_name})) { return; }

      # Check if this is the same device type
      # Create new instance if it is not.
      if (defined($device_ref[$dev_num])) {
         if ($device_ref[$dev_num]{device} ne $device_name) {
            delete($device_ref[$dev_num]);
            $device_ref[$dev_num] = $device_name->new();
            $device_ref[$dev_num]{dev_num} = $dev_num;
         }
      }
      else {
         $device_ref[$dev_num] = $device_name->new();
         $device_ref[$dev_num]{dev_num} = $dev_num;
      }

      @chan_list = @{$device_ref[$dev_num]{fields}};

      $chan_num = 0;
      foreach $channel (@chan_list) {
         $dispitem[$row][$col]=$frame->Label(
            -anchor => 'w',
            -text => $device_ref[$dev_num]{label}{$channel},
          # -width => 15,
            -font => @font,
         )-> grid(-row=>$row, -column=>$col, -padx=>3, -sticky=>'e');

         $dispitem[$row][$col+1]=$frame->Label(
            -anchor => 'w',
            -textvariable => \$display[$dev_num]{$channel},
            -width => 15,
            -font => @font,
         )-> grid(-row=>$row, -column=>$col+1, -sticky=>'w');

         $chan_num++;
         $row++;
      }
      $col += 2;
   }
}

sub update_display {
   # Copies the data from the %data hash to the array linked to
   # the display items, display_data[device number]{channel name}

   my ($dev_num, $chan_num, $chan, @chan_list, $device_name);
   my ($num_devices) = $config_data{modules}{number};

   # Schedule next call to this function
   $timed_events{update_display}->after(1000/$config_data{general}{update_display_rate}, \&update_display);

   for ($dev_num = 0; $dev_num < $num_devices ; $dev_num++) {
      $device_name = $device_type[$dev_num];

      next if ($device_name eq 'None'); # Skip 'None' device

      @chan_list = @{$devices{$device_name}{fields}}; 
      $chan_num = 0;
      foreach $chan (@chan_list) {
         $display[$dev_num]{$chan} = $device_ref[$dev_num]{data}{$chan};
         $chan_num++;
      }
   }
}


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

sub read_config_file {
   my ($ini_filename) = @_;
   my ($line, $parameter, $settings);
   my (%tmp_hash);

   open(INIFILE, "<$ini_filename") or return set_default_values();
   
   while (<INIFILE>) {
      $line = $_;
      $line =~ s/\x0a//;
      $line =~ s/\x0d//;
      ($parameter, $settings) = split(/\t/, $line);
      
      $tmp_hash{$parameter} = eval("{$settings}");
   }

   close(INIFILE);
   
   return(%tmp_hash);
}

sub save_config_file {

   my ($dev_num);
   my ($num_devices) = $config_data{modules}{number};

   $config_data{window}{height} = $mw->height;
   $config_data{window}{width} = $mw->width;
   $config_data{window}{xpos} = $mw->x;
   $config_data{window}{ypos} = $mw->y;

   # Update device and com port settings
   $config_data{modules}{active_list} = ();
   $config_data{modules}{comports} = ();
   for ($dev_num = 0; $dev_num < $num_devices ; $dev_num++) {
      $config_data{modules}{active_list}[$dev_num] = $device_type[$dev_num];
      $config_data{modules}{comports}[$dev_num] = $com_list[$dev_num];
   }

   my ($section, @section_list, $key, $val, $item);
   open(INIFILE, '>' . $config_file);
   
   # List of sections for main program to save
   @section_list = ('general', 'window', 'modules');

   foreach $section (@section_list) {
      print INIFILE "$section\t";
      while (($key, $val) = each(%{$config_data{$section}})) {
         # Test if this is an array
         if (eval{"$val->[0];"}) { 
            # $val is array
            print INIFILE "$key=>[";
            foreach $item (@{$val}) {
               print INIFILE "'$item', ";
            }
            print INIFILE "], ";
         }
         else {
            # $val is scalar
            print INIFILE "$key=>'$val', ";
         }
      }
      print INIFILE "\n";
   }
   
   my ($device);
   foreach $device (@device_list) {
      print INIFILE "$device\t";
      print INIFILE $device->config_save();
   }

   close(INIFILE);
}

# Reset all config values to defaults
sub set_default_values {
   my (%hashdata) = ();

   $hashdata{general}{save_log_data_rate} = '4';
   $hashdata{general}{update_display_rate} ='5';
   $hashdata{general}{simulate} = '1';
   $hashdata{general}{font_size} = '10';
   $hashdata{general}{scan_data_rate} = '20';

   $hashdata{window}{width} = '527';
   $hashdata{window}{xpos} = '127';
   $hashdata{window}{ypos} = '84';
   $hashdata{window}{height} = '396';

   $hashdata{modules}{comports} = ['None', 'None', ];
   $hashdata{modules}{active_list} = ['None', 'None', ];
   $hashdata{modules}{number} = '2';

   # Get default setup data from each of the modules
   my ($device);
   foreach $device (@device_list) {
      $hashdata{$device} = $device->set_default_values();
   }
   
   return %hashdata;
}

sub user_config {
   my @modules = keys(%devices);
   my ($module, @list);
   my %page;
   my ($row, $col, $i);

   my (%temphash) = %config_data;

   my $dialog = $mw->DialogBox(-title => "Setup", -buttons => ["Save", "Cancel"]);

   # Add a notebook widget to dialogbox
   my $nb = $dialog->add('NoteBook')->pack(-expand => 1, -fill => 'both');

   # List of items that will appear in 'General' tab 
   my @tmp_config_array = (
      ["entry", "Number of Devices",        \$temphash{modules}{number} ],
      ["entry", "Font size",                \$temphash{general}{font_size} ],
      ["entry", "Device Scan Rate (#/sec)",    \$temphash{general}{scan_data_rate} ],
      ["entry", "Log File Save Rate (#/sec)",  \$temphash{general}{save_log_data_rate} ],
      ["entry", "Display Update Rate(#/sec)",  \$temphash{general}{update_display_rate} ],
      ["label", "" ],
      ["check", "Simulated data from file", \$temphash{general}{simulate} ],
   );
   
   $row = 0;
   $col = 0;

   my $page_name = 'General';
   my $config_item;
   # Setup 'General' page of notebook

   $page{$page_name}{page} = $nb->add('Page 1', -label => 'General');

   foreach $config_item (@tmp_config_array) {
      if (@{$config_item}[0] eq 'entry') {
         # Add label/entry widget pair
         $page{$page_name}{page}->Label(
            -text => @{$config_item}[1],
         )->grid(-row => $row, -column=> $col);
         $page{$page_name}{page}->Entry(
            -textvariable => @{$config_item}[2],
            -width => 6,
         )->grid(-row => $row, -column=> $col+1, -pady => 2);
      }
      elsif (@{$config_item}[0] eq 'label') {
         # Add label/entry widget pair
         $page{$page_name}{page}->Label(
            -text => @{$config_item}[1],
         )->grid(-row => $row, -column=> $col);
      }
      elsif (@{$config_item}[0] eq 'check') {
         $page{$page_name}{page}->Checkbutton(
            -text => @{$config_item}[1],
            -variable => @{$config_item}[2],
         )->grid(-row => $row, -column=> $col, -pady => 2, -columnspan => 2);
      }
      $row++;
   }

   # Add a page to notebook for each loaded module
   foreach $module (@modules) {
      $module->config_screen($nb)
   }

   if ($dialog->Show eq "Save") { # Save config data if user pressed 'Save'
      %config_data = %temphash;

      foreach $module (@modules) {
         # Make a page for each module loaded
         $module->config_save();
      }
      
      save_config_file();
      disp_chanlist();
   }
}
