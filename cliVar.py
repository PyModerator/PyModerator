#
# Client side global variables and some mutable "constants".
#

import commonDefs

# Change the client configuration database path if the need arises.
path = "./ClientDB"

sockFile = None                 # The socket connection to the server.
app = None                      # The PyModeratorClient instance is main app.
svr = commonDefs.ServerData()   # Local copy of the server's main database.
currentNewsGroup = None         # Currently active newsgroup.
currentNewsGroupID = ""         # Currently active newsgroup ID.
thisModerator = None            # Current moderator.
thisModeratorID = ""            # Current moderator ID.

appVersion = "0.31"
