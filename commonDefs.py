#
# This defines data structures that are passed between the clients and the
# server. It is imported by both sides.
#

import sys
import time
import types
import string
import nntplib
import smtplib
import io

#------------------------------------------------------------------------------
# Utility routines used on client and server.

def TimeNow():
    return time.time()

def LocalTimeSm(unixTime):
    if unixTime:
        return time.strftime("%m/%d %H:%M", time.localtime(unixTime))
    else:
        return "--/-- --:--"

def LocalTimeRg(unixTime):
    if unixTime:
        return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(unixTime))
    else:
        return "----/--/-- --:--:--"

def WordWrap(inpLines):
    outLines = []
    for aline in inpLines:
        while len(aline) > 80:
            idx = 79
            while idx >= 0 and aline[idx] not in string.whitespace:
                idx = idx - 1
            if idx < 0:
                idx = 80
                while idx < len(aline) and aline[idx] not in string.whitespace:
                    idx = idx + 1
            outLines.append(aline[:idx])
            if idx >= len(aline):
                aline = None
                break
            else:
                aline = aline[idx + 1:]
        if aline != None:
            outLines.append(aline)
    return outLines

def CleanCut(argStr, argLen):
    if len(argStr) > argLen:
        ec = argStr[argLen]
        argStr = argStr[:argLen]
        if ec not in string.whitespace:
            tmpStr = " ".join(argStr.split(" ")[:-1])
            if len(tmpStr) > 0:
                argStr = tmpStr
    return argStr

class CmdError(Exception):
    def __init__(self, details):
        self.details = details

    def __str__(self):
        return self.details

def EmptySummary(messageID, status):
    return ("-", messageID, status, "", None, "")

def EmailMessage(toAddrs, outHeaders, outTxt, smtpHost):
    fromAddr = outHeaders.get(("From", 0), "")
    hdrs = list(outHeaders.items())
    msg = ""
    hdrs.sort()
    for hdr in hdrs:
        msg = "%s%s: %s\n" % (msg, hdr[0][0], hdr[1])
    msg = "%s\n%s" % (msg, outTxt)
    errMsg = ""
    try:
        smtpServer = smtplib.SMTP()
        #smtpServer.set_debuglevel(1)
        smtpServer.connect(smtpHost)
        smtpServer.sendmail(fromAddr, toAddrs, msg)
        smtpServer.quit()
    except:
        errMsg = "ERROR! Message not sent: %s" % sys.exc_info()[1]
    return msg, errMsg

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
        nntpDst.post(io.BytesIO(msg.encode('utf-8')))
    except (nntplib.NNTPReplyError, nntplib.NNTPTemporaryError,
            nntplib.NNTPPermanentError, nntplib.NNTPProtocolError) as val:
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
        self.idleTimeLogout = 900

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
    def __init__(self, name = "", fromAddress = "", vacation = 0):
        self.name = name
        self.fromAddress = fromAddress
        self.vacation = vacation

    def __repr__(s):
        return Rep(s)

class ModeratorROData:
    def __init__(self, moderatorID):
        self.moderatorID = moderatorID
        self.createTime = TimeNow()
        self.currentNewsGroupID = ""
        self.lastLogin = None
        self.lastLogout = None
        self.loggedIn = 0
        self.userType = "Moderator" # "Superuser", "Guest"
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
    def __init__(self, popHost = "", popPort = 110, popUserID = "", popSSL = 0,
                    popPassword = "", allowCrossPosts = 0, roundRobinAssign = 0,
                    postFromServer = 0):
        self.popHost = popHost
        self.popPort = popPort
        self.popSSL = popSSL
        self.popUserID = popUserID
        self.popPassword = popPassword
        self.allowCrossPosts = allowCrossPosts
        self.roundRobinAssign = roundRobinAssign
        self.postFromServer = postFromServer
        self.periodicPosts = { }    # {messageID: [nextSendTime, repeatTime]}
        self.quotingYellow = 25
        self.quotingRed = 10

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
        # statistics = {moderatorID: [column0, ...]}
        self.statistics = {"": ["Approved", "Limboed"] }

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
        self.newMaterial = 100
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

