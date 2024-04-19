#!/usr/bin/env python
#
# This is the script that is use to start up the server.
#

import sys
import traceback

try:
    import serverPyModerator
    serverPyModerator.Main()
except:
    t, v, tb = sys.exc_info()
    traceback.print_exception(t, v, tb)
    print("The program was terminated or failed to start properly. Please")
    print("check your installation and if you continue to have problems,")
    print("send a copy of the above error information to JamesL@Lugoj.com.")
    input("(Please press enter when you have finished viewing.)")
