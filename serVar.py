#
# Server side global variables.
#

# Change the server database data file path if the need arises.
path = "./ServerDB"

app = None              # Server instance serves as main application object.
validNewsGroupIDs = { } # { newsGroupID : flag } where flag = y, n, or m
updateSchedule = 1      # Set when schedule change needs to be made.

appVersion = "0.31"
