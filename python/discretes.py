#! /sw/bin/python2.4

# The event marker state is checked about 50 times per second, to be sure to 
# catch momentary event marker hits.  If the event marker is HIGH, a flag is
# latched.  If the flag is set when it is time to record data, the event marker
# is recorded as ON, and the flag is reset to LOW.
#
# This version only captures the event marker, which must be a voltage source
# connected to pin 1 of the serial port.  It could be extended to three other 
# discretes:
#   pin 6, captured by data_source.getDSR()
#   pin 8, captured by data_source.getCTS()
#   pin 9, captured by data_source.getRI()


from __future__ import division
import time
import os.path
# import Queue


class Discretes:
    device_name = 'Discretes'
    baudrate = 9600
    bytesize    = 'EIGHTBITS'
    parity      = 'N'
    stopbits    =  1
    timeout     =  1
    xonxoff     =  0
    rtscts      =  0
    data_to_record   = {'EVENT': 1}
    order_label_units = [('EVENT','Event Marker','1 = Event')]
    scaling          =  {'EVENT': 1}


def grab_discrete_data(test_mode, data_rate, duration, serial_list, outputs, ):
    if test_mode == '0':
        data_source = serial_list['Discretes']
        print 'Starting discretes thread.  Test mode =', test_mode, 'Data source is:', data_source
    else:
        print 'Starting discretes thread.  Test mode =', test_mode, 'There is no data source.'
        
    # check event marker state about 50 times a second
    sleep_time = 1.0 / 50.0
    
    start_time = time.time()
    raw_count = start_time * data_rate
    count = int(raw_count)
    data_time = start_time
    end_time = start_time + duration * 60
    event_flag = False
    while data_time < end_time:
        data_time = time.time()
        data_count = data_time * data_rate
        if test_mode == '0':
            event_state = data_source.getCD()
        else:
            event_state = '0'
        if event_state:
            event_flag = True
        time.sleep(sleep_time)
        if data_count >= count:
        # time to record
            if event_flag:
                data_string = str(data_time) + '\t' + '1' + '\n'
                event_flag = False
                print 'Event Marker ON',
            else:
                data_string = str(data_time) + '\t' + '0' + '\n'
                
            count = count + 1
                        
            outputs['Discretes'].write(data_string)
#           queues['Discretes'].put(data_string)
    
            # has the main thread sent a stop flag?
            if os.path.exists('stop_recording.flag'):
                print 'Discretes data recording stopping'
                outputs['Discretes'].close()
                return
    print 'Discretes recording shutting down'
    outputs['Discretes'].close()
