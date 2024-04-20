#
# These are classes and functions that manipulate the database files. They
# assume authentication has been done elsewhere, but the functions do
# not assume the arguments are valid and run validation checks on them.
#
# The segregation of classes and functions bwtween this module and the
# serverPyModerator module needs a lot of cleaning up. Perhaps they should
# simply be merged together.
#

import time
import pickle
import hashlib
import os
import nntplib
import poplib
import serVar
import io
import socket
from commonDefs import *

IndexRecLen = 38

def Crypt(password):
    return hashlib.sha1(password.encode('utf-8')).hexdigest()

class ServerApp(ServerData):
    def __init__(self):
        self.fn = "%s/server.cfg" % serVar.path
        if not os.path.exists(serVar.path):
            os.mkdir(serVar.path)
        try:
            self.dataFile = open(self.fn, "rb+")
            self.Read()
        except IOError:
            ServerData.__init__(self)
            self.cryptedPasswords = { }
            self.dataFile = open(self.fn, "wb+")
            rootUser = ModeratorData("root", ModeratorRWData("root"))
            rootUser.ro.userType = "Superuser"
            self.NewModerator("", rootUser)
            self.Write()
        # Locked files indicators do not persist.
        self.lockedMessages = { } # {messageID: moderatorID}
        self.newsGroupFiles = { }
        for newsGroupID in self.ro.newsGroupIDs:
            self.newsGroupFiles[newsGroupID] = NewsGroupFile(newsGroupID)
        # Logged-in flag does not persist.
        for moderator in list(self.ro.moderators.values()):
            moderator.ro.loggedIn = 0
        try:
            self.ReadValidGroups()
        except IOError:
            self.WriteValidGroups()

    def ReadValidGroups(self):
        validGrpsFile = open("%s/validGroups" % serVar.path, "rb+")
        serVar.validNewsGroupIDs = pickle.load(validGrpsFile)
        validGrpsFile.close()

    def WriteValidGroups(self):
        validGrpsFile = open("%s/validGroups" % serVar.path, "wb+")
        pickle.dump(serVar.validNewsGroupIDs, validGrpsFile, 1)
        validGrpsFile.close()

    def Read(self):
        self.dataFile.seek(0)
        appVersion = pickle.load(self.dataFile)
        (self.ro, self.rw, self.cryptedPasswords) = pickle.load(self.dataFile)

    def Write(self):
        self.dataFile.seek(0)
        pickle.dump(serVar.appVersion, self.dataFile, 1)
        pickle.dump((self.ro, self.rw, self.cryptedPasswords),self.dataFile, 1)
        self.dataFile.flush()

    def AddModeratorToNewsGroup(self, moderatorID, newsGroupID):
        newsGroupFile = self.newsGroupFiles.get(newsGroupID)
        if newsGroupFile == None:
            raise CmdError("Newsgroup '%s' not found." % newsGroupID)
        moderator = self.ro.moderators.get(moderatorID)
        if moderator == None:
            raise CmdError("Moderator '%s' not found." % moderatorID)
        newsGroupData = newsGroupFile.newsGroupData
        if moderatorID in newsGroupData.ro.moderatorIDs:
            raise CmdError("Moderator '%s' already in newsgroup '%s'." %
                            (moderatorID, newsGroupID))
        moderatorIDs = newsGroupData.ro.moderatorIDs
        moderatorIDs.append(moderatorID)
        moderatorIDs.sort()
        newsGroupIDs = moderator.ro.newsGroupIDs
        newsGroupIDs.append(newsGroupID)
        newsGroupIDs.sort()
        newsGroupFile.WriteData()

    def DelModeratorFromNewsGroup(self, moderatorID, newsGroupID):
        newsGroupFile = self.newsGroupFiles.get(newsGroupID)
        if newsGroupFile == None:
            raise CmdError("Newsgroup '%s' not found." % newsGroupID)
        moderator = self.ro.moderators.get(moderatorID)
        if moderator == None:
            raise CmdError("Moderator '%s' not found." % moderatorID)
        newsGroupData = newsGroupFile.newsGroupData
        moderatorIDs = newsGroupData.ro.moderatorIDs
        if moderatorID not in moderatorIDs:
            raise CmdError("Moderator '%s' not in newsgroup '%s'." %
                            (moderatorID, newsGroupID))
        if moderator.ro.currentNewsGroupID == newsGroupID:
            moderator.ro.currentNewsGroupID = ""
        moderatorIDs.remove(moderatorID)
        moderator.ro.newsGroupIDs.remove(newsGroupID)
        newsGroupFile.WriteData()

    def NewModerator(self, password, moderatorData):
        moderatorID = moderatorData.ro.moderatorID
        if moderatorID in self.ro.moderators:
            raise CmdError("Moderator '%s' already exists." % moderatorID)
        if not moderatorID:
            raise CmdError("Blank moderator ID not allowed.")
        self.ro.moderators[moderatorID] = moderatorData
        self.cryptedPasswords[moderatorID] = Crypt(password)

    def DelModerator(self, moderatorID):
        if moderatorID == "root":
            raise CmdError("User 'root' may not be deleted.")
        moderator = self.ro.moderators.get(moderatorID)
        if moderator == None:
            return
        if moderator.ro.loggedIn:
            raise CmdError("Moderator '%s' logged in; may not delete." %
                            moderatorID)
        for newsGroupID in moderator.ro.newsGroupIDs:
            newsGroupFile = self.newsGroupFiles.get(newsGroupID)
            if newsGroupFile:
                moderatorIDs = newsGroupFile.newsGroupData.ro.moderatorIDs
                if moderatorID in moderatorIDs:
                    moderatorIDs.remove(moderatorID)
        del self.cryptedPassword[moderatorID]
        del self.ro.moderators[moderatorID]

    def NewNewsGroup(self, newsGroupData):
        newsGroupID = newsGroupData.ro.newsGroupID
        if newsGroupID in self.newsGroupFiles:
            raise CmdError("Newsgroup '%s' already exists." % newsGroupID)
        if not newsGroupID:
            raise CmdError("Blank newsgroup ID not allowed.")
        self.newsGroupFiles[newsGroupID] = newsGroupFile = \
                    NewsGroupFile(newsGroupID, newsGroupData)
        newsGroupIDs = self.ro.newsGroupIDs
        newsGroupIDs.append(newsGroupID)
        newsGroupIDs.sort()
        newsGroupFile.WriteData()

    def DelNewsGroup(self, newsGroupID):
        newsGroupFile = self.newsGroupFiles.get(newsGroupID)
        if newsGroupFile == None:
            raise CmdError("Newsgroup '%s' not found." % newsGroupID)
        newsGroupData = newsGroupFile.newsGroupData
        for moderatorID in newsGroupData.ro.moderatorIDs:
            moderatorRO = self.ro.moderators[moderatorID].ro
            if newsGroupID == moderatorRO.currentNewsGroupID:
                moderatorRO.currentNewsGroupID = ""
            newsGroupIDs = moderatorRO.newsGroupIDs
            if newsGroupID in newsGroupIDs:
                newsGroupIDs.remove(newsGroupID)
        newsGroupFile.DeleteFiles()
        del self.newsGroupFiles[newsGroupID]
        self.ro.newsGroupIDs.remove(newsGroupID)

# Parses a list of message lines and returns the header lines as a dictionary
# and a string that contains the body of the message. Also capitalizes the
# header names such that the first character is caps and all others lower.
# E.g. Input "hdr1: val9" returns { ("Hdr1", 0) : "val9" }
def ParseMessageLines(txtLines):
    # Grab all lines up to first blank line.
    blankLine = txtLines.index("")
    hdr = txtLines[:blankLine]
    body = txtLines[blankLine:]
    j = 0
    for i in range(len(hdr)):
        if " " == hdr[i][0] or "\011" == hdr[i][0]:   # Space or tab
            # If leading space or tab, append left-stripped line to previous.
            hdr[j] = hdr[j] + string.lstrip(hdr[i])
            hdr[i] = None
        else:
            j = i
    # Remove all blank lines from hdr.
    hdr = [_f for _f in hdr if _f]
    # Construct headers dictionary.
    hdrDict = { }
    for hdrLine in hdr:
        colon = string.index(hdrLine, ":")
        hdrName = string.capitalize(string.rstrip(hdrLine[:colon]))
        hdrValue = string.lstrip(hdrLine[colon + 1:])
        # Header names may be repeated, (e.g. Received), so make unique key.
        idx = 0
        while (hdrName, idx) in hdrDict:
            idx = idx + 1
        hdrDict[(hdrName, idx)] = hdrValue
    # Also replace any embedded nulls with newlines as a precaution.
    return hdrDict, string.replace(string.join(body, "\n"), "\000", "\n")

def CheckCrossPosting(newsGroup, headers):
    allowCrossPosts = newsGroup.rw.allowCrossPosts
    newsGroupID = newsGroup.ro.newsGroupID
    val = headers.get(("Newsgroups", 0))
    badgroups = ""
    if val != None:
        newsgroups = [_f for _f in map(string.strip, string.split(val, ",")) if _f]
        for grp in newsgroups:
            flag = serVar.validNewsGroupIDs.get(grp)
            if grp != newsGroupID:
                if flag != "y" or not allowCrossPosts:
                    badgroups = "%s%s: %s, " % (badgroups, grp,
                                            string.capitalize(str(flag)))
        if badgroups:
            badgroups = badgroups[:-2]
    return badgroups

def ReadPOPMailbox(newsGroupID):
    app = serVar.app
    newsGroupFile = app.newsGroupFiles[newsGroupID]
    newsGroupRW = newsGroupFile.newsGroupData.rw
    if not newsGroupRW.popHost:
        return 0
    try:
        popServer = poplib.POP3(newsGroupRW.popHost, newsGroupRW.popPort)
        popServer.getwelcome()
        popServer.user(newsGroupRW.popUserID)
        popServer.pass_(newsGroupRW.popPassword)
        numMsgs, popStat = popServer.stat()
    except socket.error as val:
        raise CmdError("Failed to connect to POP mail server: %s" % val[1])
    except poplib.error_proto as val:
        raise CmdError("POP mail protocol failure: %s" % val)
    for idx in range(numMsgs):
        popMsg = popServer.retr(idx + 1)
        inHeaders, inTxt = ParseMessageLines(popMsg[1])
        messageRW = MessageRWData(inTxt, inHeaders)
        messageID = newsGroupFile.NewMessage(messageRW,
                EventData("root", EventRWData("Assigned")), 1)
        popServer.dele(idx + 1)
    popServer.quit()
    newsGroupFile.WriteData()
    app.Write()
    return numMsgs

class NewsGroupFile:
    def __init__(self, newsGroupID, newsGroupData = None):
        if newsGroupID == None:
            raise CmdError("Server Error! Blank NewsGroupFile attempt!")
        self.baseDir = "%s/%s" % (serVar.path, newsGroupID)
        self.baseCfg = "%s/%s" % (self.baseDir, "newsGroupData.cfg")
        if not os.path.exists(self.baseDir):
            os.mkdir(self.baseDir)
        try:
            self.dataFile = open(self.baseCfg, "rb+")
            self.ReadData()
        except IOError:
            self.dataFile = open(self.baseCfg, "wb+")
            self.newsGroupData = newsGroupData
            self.WriteData()

    def DeleteFiles(self):
        self.dataFile.close()
        for messageID in range(self.newsGroupData.ro.numMessages):
            self.DeleteMessageFile(messageID)
        try:
            os.unlink(self.baseCfg)
            os.rmdir(self.baseDir)
        except OSError:
            pass

    def DeleteMessageFile(self, messageID):
        try:
            os.unlink("%s/%06d" % (self.baseDir, messageID))
        except OSError:
            pass

    def ReadData(self):
        self.dataFile.seek(0)
        self.newsGroupData = pickle.load(self.dataFile)

    def WriteData(self):
        self.dataFile.seek(0)
        pickle.dump(self.newsGroupData, self.dataFile, 1)
        self.dataFile.flush()

    def NextMessageID(self):
        messageID = self.newsGroupData.ro.numMessages
        while os.path.exists("%s/%06d" % (self.baseDir, messageID)):
            messageID = messageID + 1
        self.newsGroupData.ro.numMessages = messageID + 1
        return messageID

    def ReadMessage(self, messageID):
        try:
            msg = pickle.load(open("%s/%06d" %
                                (self.baseDir, messageID), "rb+"))
        except IOError:
            raise CmdError("Invalid message ID '%d'." % messageID)
        return msg

    def WriteMessage(self, message):
        messageID = message.ro.messageID
        try:
            pickle.dump(message,
                        open("%s/%06d" % (self.baseDir, messageID), "wb+"), 1)
        except IOError:
            raise CmdError("Unable to update message ID '%d'." % messageID)

    def NewMessage(self, messageRW, evt0, assign):
        newsGroupRO = self.newsGroupData.ro
        newsGroupRW = self.newsGroupData.rw
        messageID = self.NextMessageID()
        message = MessageData(messageID, [ evt0 ], "", { }, messageRW)
        if assign and newsGroupRW.roundRobinAssign:
            moderatorIDs = newsGroupRO.moderatorIDs
            numModerators = len(moderatorIDs)
            for i in range(numModerators):
                nextModerator = newsGroupRO.nextModerator % numModerators
                giveToID = moderatorIDs[nextModerator]
                newsGroupRO.nextModerator = (nextModerator + 1) % numModerators
                moderator = serVar.app.ro.moderators.get(giveToID)
                if moderator and moderator.ro.userType != "Guest":
                    if not moderator.rw.vacation:
                        evt0.ro.moderatorID = giveToID
                        break
        message.ro.assignedTo = evt0.ro.moderatorID
        message.ro.newMaterial = NewMaterial(messageRW.inTxt)
        message.ro.badCrossPosts = \
            CheckCrossPosting(self.newsGroupData, messageRW.inHeaders)
        newsGroupRO.review.append(messageID)
        self.WriteMessage(message)
        return messageID

    def ProcessMessage(self, messageID, outTxt, outHeaders,
                            rejectID, details, moderatorID):
        newsGroupRO = self.newsGroupData.ro
        newsGroupRW = self.newsGroupData.rw
        message = self.ReadMessage(messageID)
        limbo = newsGroupRO.limbo
        review = newsGroupRO.review
        if message.ro.status in ["Rejected", "Approved"]:
            raise CmdError("Message '%d' already processed." % messageID)
        if rejectID:
            message.ro.status = "Rejected"
            eventRW = EventRWData("Reject: " + rejectID, details)
        else:
            if newsGroupRW.postFromServer:
                rw = serVar.app.rw
                PostMessage(outHeaders, outTxt, rw.nntpHost, rw.nntpPort,
                                rw.nntpUser, rw.nntpPassword)
            message.ro.status = "Approved"
            message.ro.outTxt = outTxt
            message.ro.outHeaders = outHeaders
            eventRW = EventRWData("Approved", details)
        message.ro.events[0:0] = [ EventData(moderatorID, eventRW) ]
        if messageID in limbo:
            limbo.remove(messageID)
        if messageID in review:
            review.remove(messageID)
        rejection = newsGroupRO.rejections.get(rejectID)
        if rejection:
            if rejection.rw.defaultAction == "Limbo & Reply":
                limbo.append(messageID)
                message.ro.status = "Limbo"
        self.WriteMessage(message)

    def WriteMessageEvent(self, messageID, eventRW, moderatorID):
        message = self.ReadMessage(messageID)
        message.ro.events[0:0] = [ EventData(moderatorID, eventRW) ]
        self.WriteMessage(message)

# Archive search support functions that return strings corresponding to the
# selected item names.

def IncomingHdrStr(msg):
    return string.join(list(msg.rw.inHeaders.values()), "\n")

def IncomingBdyStr(msg):
    return msg.rw.inTxt

def OutgoingHdrStr(msg):
    return string.join(list(msg.ro.outHeaders.values()), "\n")

def OutgoingBdyStr(msg):
    return msg.ro.outTxt

def HistoryEventsStr(msg):
    resp = ""
    for event in msg.ro.events:
        # resp = "%s\n%s\n%s\n%s\n%s" % (resp, LocalTimeSm(event.ro.timeStamp),
        #  event.rw.eventType, event.rw.eventDetail, event.ro.moderatorID)
        resp = "%s\n%s\n%s\n%s" % (resp, event.rw.eventType,
                                    event.rw.eventDetail, event.ro.moderatorID)
    return resp

searchFuncs = \
        {
            "Incoming Headers": IncomingHdrStr,
            "Incoming Bodies": IncomingBdyStr,
            "Outgoing Headers": OutgoingHdrStr,
            "Outgoing Bodies": OutgoingBdyStr,
            "History Events": HistoryEventsStr
        }

def GetSearchableString(message, itemNames):
    resp = ""
    for itemName in itemNames:
        func = searchFuncs.get(itemName)
        if func:
            resp = "%s\n%s" % (resp, func(message))
    return resp

def GetSummary(msg):
    fromAddress = msg.rw.inHeaders.get(("From", 0))
    if not fromAddress:
        fromAddress = msg.rw.inHeaders.get(("Reply-to", 0))
        if not fromAddress:
            fromAddress = ""
    subject = msg.rw.inHeaders.get(("Subject", 0))
    if not subject:
        subject = ""
    return (msg.ro.assignedTo, msg.ro.messageID, msg.ro.status, subject,
            msg.ro.events[-1].ro.timeStamp, fromAddress)

