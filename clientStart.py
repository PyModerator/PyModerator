#!/usr/bin/env python
#
# This is the script that should be used to start the client interface.
#

import sys
import traceback

try:
    import clientPyModerator
    clientPyModerator.Main()
except:
    t, v, tb = sys.exc_info()
    traceback.print_exception(t, v, tb)
    print "The program was terminated or failed to start properly. Please"
    print "check your installation and if you continue to have problems,"
    print "send a copy of the above error information to JamesL@Lugoj.com."
    raw_input("(Please press enter when you have finished viewing.)")

