#!/usr/bin/env python
#
# This is the script that may be used to start both the client interface and
# the server in their own threads on the same platform. Useful for solo
# moderation and testing.
#

import sys
import traceback

try:
    import thread
    import clientPyModerator
    import serverPyModerator
    thread.start_new_thread(serverPyModerator.Main, ())
    clientPyModerator.Main()
except:
    print sys.exc_info()[0]
    print sys.exc_info()[1]
    traceback.print_tb(sys.exc_info()[2])
    print "The program was terminated or failed to start properly. Please"
    print "check your installation and if you continue to have problems,"
    print "send a copy of the above error information to JamesL@Lugoj.com."
    raw_input("(Please press enter when you have finished viewing.)")

