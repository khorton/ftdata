#!/usr/bin/env python
"""
Application to control flight test data recording.
"""

import gtk
import gtk.glade


class Record_FT_Data:
    """
    Main class for flt test data recording application
    """
    def __init__(self):
        # Set the Glade file
        self.gladefile = "ftdata_control.glade"  
        self.wTree = gtk.glade.XML(self.gladefile, "main_window") 

        # Signals, and the handlers that are called
        dic = { "on_main_window_destroy" : gtk.main_quit,
            "on_quit1_activate" : gtk.main_quit }
        self.wTree.signal_autoconnect(dic)

        # from http://www.async.com.br/faq/pygtk/index.py?req=edit&file=faq22.004.htp
        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            # make sure we don't clobber existing attributes
            assert not hasattr(self, name)
            setattr(self, name, w)


if __name__ == "__main__":
    app = Record_FT_Data()
    app.combobox_port1.append_text('EIS')
    app.combobox_port1.append_text('EFIS')

#   parse_options()

    gtk.main()

