#
# This defines data structures that are passed between the clients and the
# server. It is imported by both sides.
#

import time
import nntplib
import io

#------------------------------------------------------------------------------
# Utility routines used on client and server.

def TimeNow():
    return time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(time.time()))

class CmdError:
    def __init__(self, details):
        self.details = details

    def __str__(self):
        return self.details

def PostMessage(outHeaders, outTxt, nntpHost, nntpPort, nntpUser, nntpPassword):
    try:
        if nntpUser:
            nntpDst = nntplib.NNTP(nntpHost, nntpPort, nntpUser, nntpPassword)
        else:
            nntpDst = nntplib.NNTP(nntpHost, nntpPort)
        msg = ""
        hdrs = list(outHeaders.items())
        hdrs.sort()
        for hdr in hdrs:
            msg = "%s%s: %s\n" % (msg, hdr[0][0], hdr[1])
        msg = "%s\n%s" % (msg, outTxt)
        nntpDst.post(io.StringIO(msg))
    except (nntplib.error_reply, nntplib.error_temp, nntplib.error_perm,
            nntplib.error_proto) as val:
        raise CmdError("NNTP error to %s: '%s'" % (nntpHost, val))

def NewMaterial(inTxt):
    # Strip all leading and trailing whitespace from all lines, then
    # remove all blank lines. Put result in inLines.
    inLines = [_f.strip() for _f in inTxt.split("\n") if _f]
    newText = totalText = 0.0
    for aline in inLines:
        totalText = totalText + len(aline)
        # If it starts with ">" or "|" we count it as quoted text.
        if aline[0] not in ">|":
            newText = newText + len(aline)
    # Avoid division by zero (i.e. someone sent a blank message; new material
    # will be 0%, as expected).
    if totalText < 1.0:
        totalText = 1.0
    return int(newText*100.0/totalText)

#------------------------------------------------------------------------------
# The following utility definitions are used by the transfer classes below.

indent = ""

def Fmt(arg):
    return "%s%s=%s" % (indent, arg[0], repr(arg[1]))

def Rep(self):
    global indent
    indent = indent + "  "
    cls = self.__class__.__name__
    args = list(self.__dict__.items())
    strArgs = "\n".join(list(map(Fmt, args)))
    retval = "%s:\n%s\n" % (cls, strArgs)
    indent = indent[:-2]
    return retval
    
#------------------------------------------------------------------------------
# These are definitions of the class objects transfered between client and
# server.

class ServerRWData:
    def __init__(self):
        self.nntpHost = ""
        self.nntpPort = 119
        self.nntpUser = ""
        self.nntpPassword = ""
        self.smtpHost = ""

    def __repr__(s):
        return Rep(s)

class ServerROData:
    def __init__(self):
        self.servicePort = 11556
        self.moderators = { }
        self.newsGroupIDs = [ ]

    def __repr__(s):
        return Rep(s)

class ServerData:
    def __init__(self, server = None):
        if server == None:
            self.ro = ServerROData()
            self.rw = ServerRWData()
        else:
            self.ro = server.ro
            self.rw = server.rw

    def __repr__(s):
        return Rep(s)

#------------------------------------------------------------------------------
class ModeratorRWData:
    def __init__(self, moderatorAlias = "", alertAddress = "",
                    fromAddress = "", name = ""):
        self.moderatorAlias = moderatorAlias
        self.alertAddress = alertAddress
        self.fromAddress = fromAddress
        self.name = name

    def __repr__(s):
        return Rep(s)

class ModeratorROData:
    def __init__(self, moderatorID):
        self.moderatorID = moderatorID
        self.createTime = TimeNow()
        self.currentNewsGroupID = ""
        self.lastLogin = ""
        self.lastLogout = ""
        self.loggedIn = 0
        self.superuser = 0
        self.newsGroupIDs = [ ]

    def __repr__(s):
        return Rep(s)

class ModeratorData:
    def __init__(self, moderatorID, moderatorRW):
        self.ro = ModeratorROData(moderatorID)
        self.rw = moderatorRW

    def __repr__(s):
        return Rep(s)

#------------------------------------------------------------------------------
class NewsGroupRWData:
    def __init__(self, popHost = "", popPort = 110, popUserID = "",
                    popPassword = "", allowCrossPosts = 0,
                    roundRobinAssign = 0, idleTimeLogout = 600,
                    postFromServer = 0):
        self.popHost = popHost
        self.popPort = popPort
        self.popUserID = popUserID
        self.popPassword = popPassword
        self.allowCrossPosts = allowCrossPosts
        self.roundRobinAssign = roundRobinAssign
        self.idleTimeLogout = idleTimeLogout
        self.postFromServer = postFromServer

    def __repr__(s):
        return Rep(s)

class NewsGroupROData:
    def __init__(self, newsGroupID, creatorModeratorID):
        self.newsGroupID = newsGroupID
        self.createTime = TimeNow()
        self.creatorModeratorID = creatorModeratorID
        self.nextModerator = 0
        self.moderatorIDs = [ ]
        self.numMessages = 0
        self.review = [ ]   # [ messageID ]
        self.limbo = [ ]    # [ messageID ]
        self.rejections = { }

    def __repr__(s):
        return Rep(s)

class NewsGroupData:
    def __init__(self, newsGroupID, creatorModeratorID, newsGroupRW):
        self.ro = NewsGroupROData(newsGroupID, creatorModeratorID)
        self.rw = newsGroupRW

    def __repr__(s):
        return Rep(s)

#------------------------------------------------------------------------------
class RejectionRWData:
    def __init__(self, emailTemplate = "", defaultAction = "Reject & Reply"):
        self.emailTemplate = emailTemplate
        self.defaultAction = defaultAction

    def __repr__(s):
        return Rep(s)

class RejectionROData:
    def __init__(self, rejectionID, creatorModeratorID):
        self.rejectionID = rejectionID
        self.creatorModeratorID = creatorModeratorID
        self.createTime = TimeNow()

    def __repr__(s):
        return Rep(s)

class RejectionData:
    def __init__(self, rejectionID, creatorModeratorID, rejectionRW):
        self.ro = RejectionROData(rejectionID, creatorModeratorID)
        self.rw = rejectionRW

    def __repr__(s):
        return Rep(s)

#------------------------------------------------------------------------------
class MessageRWData:
    def __init__(self, inTxt = "", inHeaders = None):
        # inHeaders = { (Capitalizedheadername, index) : header contents }
        if inHeaders == None:
            self.inHeaders = { }
        else:
            self.inHeaders = inHeaders
        self.inTxt = inTxt

    def __repr__(s):
        return Rep(s)

class MessageROData:
    def __init__(self, messageID, events, outTxt = "", outHeaders = None):
        self.messageID = messageID
        self.outTxt = outTxt
        self.events = events
        # outHeaders = { (Capitalizedheadername, index) : header contents }
        if outHeaders == None:
            self.outHeaders = { }
        else:
            self.outHeaders = outHeaders
        self.status = "Review"  # "Limbo", "Approved", "Rejected"
        self.assignedTo = ""
        self.newMaterial = 0.0
        self.badCrossPosts = ""

    def __repr__(s):
        return Rep(s)

class MessageData:
    def __init__(self, messageID, events, outTxt, outHeaders, messageRW):
        self.ro = MessageROData(messageID, events, outTxt, outHeaders)
        self.rw = messageRW

    def __repr__(s):
        return Rep(s)

#------------------------------------------------------------------------------
class EventRWData:
    def __init__(self, eventType = "", eventDetail = ""):
        self.eventType = eventType
        self.eventDetail = eventDetail

    def __repr__(s):
        return Rep(s)

class EventROData:
    def __init__(self, moderatorID):
        self.timeStamp = TimeNow()
        self.moderatorID = moderatorID

    def __repr__(s):
        return Rep(s)

class EventData:
    def __init__(self, moderatorID, eventRW):
        self.ro = EventROData(moderatorID)
        self.rw = eventRW

    def __repr__(s):
        return Rep(s)

