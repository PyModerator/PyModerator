#
# These are the server functions that the client calls indirectly via the
# socket connection. They perform authentication and do basic stuff, but
# operations on data in the server files is done in the serverFiles module.
#
# That is the theory; in practice the serverFiles module and this one are
# in need of some serious cleanup.
#

import sys
import socket
import string
import pickle
import io
import traceback
import serVar
import nntplib
import select
import re
import struct
import asyncore
import traceback
from commonDefs import *
from serverFiles import *

validCmds = { }

def AddCmd(func):
    validCmds[func.__name__] = func

def CurrentNewsgroup(modContext):
    app = serVar.app
    newsGroupID = modContext[0].ro.currentNewsGroupID
    if not newsGroupID or newsGroupID not in app.newsGroupFiles:
        raise CmdError("Current newsgroup is not set to valid value.")
    return app.newsGroupFiles[newsGroupID]

#------------------------------------------------------------------------------
def ServerLogin(moderatorID, password, modContext):
    print("Login", moderatorID)
    app = serVar.app
    moderator = app.ro.moderators.get(moderatorID)
    if moderator != None:
        if moderator.ro.loggedIn:
            raise CmdError("Already logged in.")
        if app.cryptedPasswords[moderatorID] == Crypt(password):
            moderator.ro.lastLogin = TimeNow()
            moderator.ro.loggedIn = 1
            modContext[0] = moderator
            app.Write()
    return modContext[0]
AddCmd(ServerLogin)

def ServerSetNewsGroup(newsGroupID, modContext):
    app = serVar.app
    if newsGroupID not in modContext[0].ro.newsGroupIDs:
        raise CmdError("May not switch to newsgroup '%s'." % newsGroupID)
    modContext[0].ro.currentNewsGroupID = newsGroupID
    app.Write()
    return 1
AddCmd(ServerSetNewsGroup)

def ServerLogout(modContext):
    moderator = modContext[0]
    if moderator:
        moderator.ro.lastLogout = TimeNow()
        moderator.ro.loggedIn = 0
        moderatorID = moderator.ro.moderatorID
        print("Logout", moderatorID)
        lockedMessages = serVar.app.lockedMessages
        for messageID, modID in list(lockedMessages.items()):
            if modID == moderatorID:
                del lockedMessages[messageID]
        serVar.app.Write()
AddCmd(ServerLogout)

def ServerUpdate(serverRW, modContext):
    app = serVar.app
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Must be superuser to update values.")
    app.rw = serverRW
    app.Write()
AddCmd(ServerUpdate)

def ServerGet(modContext):
    app = serVar.app
    return ServerData(app)
AddCmd(ServerGet)

def ServerUpdateValidGroups(modContext):
    app = serVar.app
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Must be superuser to update valid group list.")
    rw = app.rw
    if rw.nntpUser:
        nntpDst = nntplib.NNTP(rw.nntpHost, rw.nntpPort, rw.nntpUser,
                               rw.nntpPassword)
    else:
        nntpDst = nntplib.NNTP(app.rw.nntpHost, app.rw.nntpPort)
    grps = nntpDst.list()[1]
    for grp in grps:
        serVar.validNewsGroupIDs[grp[0]] = grp[3]
    app.WriteValidGroups()
AddCmd(ServerUpdateValidGroups)

#------------------------------------------------------------------------------
def GetModerator(moderatorID):
    app = serVar.app
    moderator = app.ro.moderators.get(moderatorID)
    if moderator == None:
        raise CmdError("Moderator '%s' not found." % moderatorID)
    return moderator

def ModeratorCreate(moderatorID, password, moderatorRW, modContext):
    app = serVar.app
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only a superuser may create a moderator.")
    app.NewModerator(password, ModeratorData(moderatorID, moderatorRW))
    app.Write()
AddCmd(ModeratorCreate)

def ModeratorList(modContext):
    app = serVar.app
    lst = list(app.ro.moderators.keys())
    lst.sort()
    return lst
AddCmd(ModeratorList)

def ModeratorGet(moderatorID, modContext):
    return GetModerator(moderatorID)
AddCmd(ModeratorGet)

def ModeratorUpdate(moderatorID, moderatorRW, modContext):
    app = serVar.app
    moderator = GetModerator(moderatorID)
    if modContext[0].ro.userType != "Superuser":
        if modContext[0].ro.moderatorID != moderatorID:
            raise CmdError("Only superusers may modify other users.")
    moderator.rw = moderatorRW
    app.Write()
AddCmd(ModeratorUpdate)

def ModeratorChangePW(moderatorID, newPW, modContext):
    app = serVar.app
    moderator = GetModerator(moderatorID)
    if modContext[0].ro.userType != "Superuser":
        if modContext[0].ro.moderatorID != moderatorID:
            raise CmdError("Only superusers may modify other user's passwords.")
    if moderatorID == "root" and modContext[0].ro.moderatorID != moderatorID:
        raise CmdError("Only root may change root's password.")
    app.cryptedPasswords[moderatorID] = Crypt(newPW)
    app.Write()
AddCmd(ModeratorChangePW)

def ModeratorChangeType(moderatorID, userType, modContext):
    app = serVar.app
    moderator = GetModerator(moderatorID)
    if modContext[0].ro.moderatorID != "root":
        raise CmdError("Only root may change a user's type.")
    if moderatorID == "root":
        raise CmdError("Root's user type may not be changed.")
    moderator.ro.userType = userType
    app.Write()
AddCmd(ModeratorChangeType)

def ModeratorDelete(moderatorID, modContext):
    app = serVar.app
    GetModerator(moderatorID)
    if modContext[0].ro.userType != "Superuser":
        if modContext[0].ro.moderatorID != moderatorID:
            raise CmdError("Only superusers may delete other users.")
    app.DelModerator(moderatorID)
    app.Write()
AddCmd(ModeratorDelete)

#------------------------------------------------------------------------------
def GetNewsGroup(newsGroupID):
    app = serVar.app
    newsGroupFile = app.newsGroupFiles.get(newsGroupID)
    if newsGroupFile == None:
        raise CmdError("Newsgroup '%s' not found." % newsGroupID)
    return newsGroupFile

def NewsGroupCreate(newsGroupID, newsGroupRW, modContext):
    app = serVar.app
    moderatorID = modContext[0].ro.moderatorID
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may create a newsgroup.")
    app.NewNewsGroup(NewsGroupData(newsGroupID, moderatorID, newsGroupRW))
    app.Write()
AddCmd(NewsGroupCreate)

def NewsGroupGet(newsGroupID, modContext):
    return GetNewsGroup(newsGroupID).newsGroupData
AddCmd(NewsGroupGet)

def NewsGroupList(modContext):
    lst = serVar.app.ro.newsGroupIDs[:]
    lst.sort()
    return lst
AddCmd(NewsGroupList)

def NewsGroupUpdate(newsGroupID, newsGroupRW, modContext):
    app = serVar.app
    newsGroupFile = GetNewsGroup(newsGroupID)
    newsGroup = newsGroupFile.newsGroupData
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may modify newsgroups.")
    newsGroup.rw = newsGroupRW
    serVar.updateSchedule = 1
    newsGroupFile.WriteData()
    app.Write()
AddCmd(NewsGroupUpdate)

def NewsGroupDelete(newsGroupID, modContext):
    app = serVar.app
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may delete a newsgroup.")
    app.DelNewsGroup(newsGroupID)
    app.Write()
AddCmd(NewsGroupDelete)

def NewsGroupGetIncomingPosts(newsGroupID, modContext):
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not activate incoming checks.")
    GetNewsGroup(newsGroupID)
    ReadPOPMailbox(newsGroupID)
AddCmd(NewsGroupGetIncomingPosts)

def NewsGroupModerators(newsGroupID, moderatorIDs, modContext):
    app = serVar.app
    newsGroupFile = GetNewsGroup(newsGroupID)
    newsGroup = newsGroupFile.newsGroupData
    newModeratorIDs = list(moderatorIDs)
    newModeratorIDs.sort()
    oldModeratorIDs = newsGroup.ro.moderatorIDs[:]
    oldModeratorIDs.sort()
    if newModeratorIDs == oldModeratorIDs:
        return  # No change requested.
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may change newsgroup moderators.")
    for moderatorID in list(app.ro.moderators.keys()):
        if moderatorID in oldModeratorIDs:
            if moderatorID not in newModeratorIDs:
                app.DelModeratorFromNewsGroup(moderatorID, newsGroupID)
        elif moderatorID in newModeratorIDs:
            app.AddModeratorToNewsGroup(moderatorID, newsGroupID)
    newsGroupFile.WriteData()
    app.Write()
AddCmd(NewsGroupModerators)

def AddModeratorToNewsGroup(moderatorID, newsGroupID, modContext):
    app = serVar.app
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may add moderators to newsgroups.")
    app.AddModeratorToNewsGroup(moderatorID, newsGroupID)
    app.Write()
AddCmd(AddModeratorToNewsGroup)

def DelModeratorFromNewsGroup(moderatorID, newsGroupID, modContext):
    app = serVar.app
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may delete moderators from newsgroups.")
    app.DelModeratorFromNewsGroup(moderatorID, newsGroupID)
    app.Write()
AddCmd(DelModeratorFromNewsGroup)

#------------------------------------------------------------------------------
def GetRejection(rejectionID, modContext):
    app = serVar.app
    newsGroupFile = CurrentNewsgroup(modContext)
    newsGroup = newsGroupFile.newsGroupData
    rejection = newsGroup.ro.rejections.get(rejectionID)
    if rejection == None:
        raise CmdError("Rejection ID '%s' not found." % rejectionID)
    return rejection, newsGroupFile, newsGroup

def RejectionCreate(rejectionID, rejectionRW, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not create new rejection types.")
    newsGroupFile = CurrentNewsgroup(modContext)
    newsGroup = newsGroupFile.newsGroupData
    if rejectionID in newsGroup.ro.rejections:
        raise CmdError("Rejection ID '%s' already exists." % rejectionID)
    if not rejectionID:
        raise CmdError("Blank rejection ID is not allowed.")
    moderatorID = modContext[0].ro.moderatorID
    newsGroup.ro.rejections[rejectionID] = RejectionData(rejectionID,
                                                    moderatorID, rejectionRW)
    newsGroupFile.WriteData()
    app.Write()
AddCmd(RejectionCreate)

def RejectionList(modContext):
    app = serVar.app
    newsGroup = CurrentNewsgroup(modContext).newsGroupData
    lst = list(newsGroup.rejections.keys())
    lst.sort()
    return lst
AddCmd(RejectionList)

def RejectionGet(rejectionID, modContext):
    rejection, newsGroupFile, newsGroup = GetRejection(rejectionID, modContext)
    return rejection
AddCmd(RejectionGet)

def RejectionUpdate(rejectionID, rejectionRW, modContext):
    app = serVar.app
    rejection, newsGroupFile, newsGroup = GetRejection(rejectionID, modContext)
    if modContext[0].ro.userType != "Superuser":
        if modContext[0].ro.moderatorID != rejection.ro.creatorModeratorID:
            raise CmdError("Only owners or superusers may modify rejections.")
    rejection.rw = rejectionRW
    newsGroupFile.WriteData()
    app.Write()
AddCmd(RejectionUpdate)

def RejectionDelete(rejectionID, modContext):
    app = serVar.app
    rejection, newsGroupFile, newsGroup = GetRejection(rejectionID, modContext)
    if modContext[0].ro.userType != "Superuser":
        if modContext[0].ro.moderatorID != rejection.ro.creatorModeratorID:
            raise CmdError("Only owners or superusers may delete rejections.")
    del newsGroup.ro.rejections[rejectionID]
    newsGroupFile.WriteData()
    app.Write()
AddCmd(RejectionDelete)

#------------------------------------------------------------------------------
def ReviewListMessages(modContext):
    return CurrentNewsgroup(modContext).newsGroupData.ro.review
AddCmd(ReviewListMessages)

def LimboListMessages(modContext):
    return CurrentNewsgroup(modContext).newsGroupData.ro.limbo
AddCmd(LimboListMessages)

def LimboTheMessage(messageID, detail, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not place messages into limbo.")
    newsGroupFile = CurrentNewsgroup(modContext)
    newsGroupData = newsGroupFile.newsGroupData
    review = newsGroupData.ro.review
    limbo = newsGroupData.ro.limbo
    if messageID in limbo:
        raise CmdError("Message ID '%d' already in limbo." % messageID)
    message = newsGroupFile.ReadMessage(messageID)
    message.ro.status = "Limbo"
    moderatorID = modContext[0].ro.moderatorID
    eventRW = EventRWData("Limbo", detail)
    message.ro.events[0:0] = [ EventData(moderatorID, eventRW) ]
    limbo.append(messageID)
    if messageID in review:
        review.remove(messageID)
    stats = newsGroupData.ro.statistics
    modRow = stats.get(moderatorID)
    if not modRow:
        modRow = stats[moderatorID] = len(stats[""])*[ 0 ]
    modRow[1] = modRow[1] + 1
    newsGroupFile.WriteMessage(message)
    newsGroupFile.WriteData()
    app.Write()
AddCmd(LimboTheMessage)

def SearchArchive(searchExp, ignoreCase, itemNames, modContext):
    app = serVar.app
    newsGroupFile = CurrentNewsgroup(modContext)
    newsGroupData = newsGroupFile.newsGroupData
    summaries = [ ]
    if ignoreCase:
        srch = re.compile(searchExp, re.IGNORECASE | re.MULTILINE)
    else:
        srch = re.compile(searchExp, re.MULTILINE)
    for messageID in range(newsGroupData.ro.numMessages):
        try:
            message = newsGroupFile.ReadMessage(messageID)
            searchable = GetSearchableString(message, itemNames)
            if srch.search(searchable):
                summaries.append(GetSummary(message))
        except CmdError:
            pass
    return summaries
AddCmd(SearchArchive)

#------------------------------------------------------------------------------
def MessageCreate(messageRW, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not create new messages.")
    newsGroupFile = CurrentNewsgroup(modContext)
    moderatorID = modContext[0].ro.moderatorID
    messageID = newsGroupFile.NewMessage(messageRW,
                    EventData(moderatorID, EventRWData("Created")), 0)
    newsGroupFile.WriteData()
    app.Write()
    return messageID
AddCmd(MessageCreate)

def MessageSummaries(messageIDs, modContext):
    newsGroupFile = CurrentNewsgroup(modContext)
    summaries = [ ]
    for messageID in messageIDs:
        try:
            summaries.append(GetSummary(newsGroupFile.ReadMessage(messageID)))
        except CmdError:
            summaries.append(EmptySummary(messageID, "Deleted"))
    return summaries
AddCmd(MessageSummaries)

def MessageGet(messageID, modContext):
    return CurrentNewsgroup(modContext).ReadMessage(messageID)
AddCmd(MessageGet)

def MessageLock(messageID, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        return "Message not locked for guest. "
    newsGroupFile = CurrentNewsgroup(modContext)
    moderatorID = modContext[0].ro.moderatorID
    message = newsGroupFile.ReadMessage(messageID)
    lockedBy = app.lockedMessages.get(messageID)
    if lockedBy and lockedBy != moderatorID:
        return "Warning: message locked by %s. " % (lockedBy)
    # This clears all of the moderator's locks. Assumes moderators may only
    # lock one message at a time. This may be changed in the future.
    MessageUnLock(None, modContext)
    app.lockedMessages[messageID] = moderatorID
    return 1
AddCmd(MessageLock)

def MessageUnLock(messageID, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        return None
    moderatorID =  modContext[0].ro.moderatorID
    if messageID == None:
        messageIDs = list(app.lockedMessages.keys())
    else:
        if not app.lockedMessages.get(messageID):
            return None
        messageIDs = [ messageID ]
    for messageID in messageIDs:
        if app.lockedMessages[messageID] == moderatorID:
            del app.lockedMessages[messageID]
    return None
AddCmd(MessageUnLock)

def MessageReassign(messageID, assignTo, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not reassign messages.")
    newsGroupFile = CurrentNewsgroup(modContext)
    newsGroupData = newsGroupFile.newsGroupData
    message = newsGroupFile.ReadMessage(messageID)
    if assignTo != "root" and assignTo not in newsGroupData.ro.moderatorIDs:
        raise CmdError("No such moderator '%s' for this newsgroup." % assignTo)
    moderatorID = modContext[0].ro.moderatorID
    lockedBy = app.lockedMessages.get(messageID)
    if lockedBy and lockedBy != moderatorID:
        return CmdError("Error: message %d locked by %s." %
                        (messageID, lockedBy))
    message.ro.assignedTo = assignTo
    eventRW = EventRWData("Reassign", "Reassigned to %s." % assignTo)
    message.ro.events[0:0] = [ EventData(moderatorID, eventRW) ]
    newsGroupFile.WriteMessage(message)
    newsGroupFile.WriteData()
    app.Write()
AddCmd(MessageReassign)

def MessageAddEvent(messageID, eventRW, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not add events to messages.")
    newsGroupFile = CurrentNewsgroup(modContext)
    moderatorID = modContext[0].ro.moderatorID
    newsGroupFile.WriteMessageEvent(messageID, eventRW, moderatorID)
    newsGroupFile.WriteData()
    app.Write()
AddCmd(MessageAddEvent)

def MessageApprove(messageID, outTxt, outHeaders, details, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not approve messages.")
    newsGroupFile = CurrentNewsgroup(modContext)
    moderatorID = modContext[0].ro.moderatorID
    lockedBy = app.lockedMessages.get(messageID)
    if lockedBy and lockedBy != moderatorID:
        return CmdError("Error: message %d locked by %s." %
                        (messageID, lockedBy))
    newsGroupFile.ProcessMessage(messageID, outTxt, outHeaders,
                                None, details, moderatorID)
    stats = newsGroupFile.newsGroupData.ro.statistics
    modRow = stats.get(moderatorID)
    if not modRow:
        modRow = stats[moderatorID] = len(stats[""])*[ 0 ]
    modRow[0] = modRow[0] + 1
    newsGroupFile.WriteData()
    app.Write()
AddCmd(MessageApprove)

def MessageReject(messageID, rejectID, details, modContext):
    app = serVar.app
    if modContext[0].ro.userType == "Guest":
        raise CmdError("Guests may not reject messages.")
    newsGroupFile = CurrentNewsgroup(modContext)
    moderatorID = modContext[0].ro.moderatorID
    lockedBy = app.lockedMessages.get(messageID)
    if lockedBy and lockedBy != moderatorID:
        return CmdError("Error: message %d locked by %s." %
                        (messageID, lockedBy))
    newsGroupFile.ProcessMessage(messageID, "", { },
                                rejectID, details, moderatorID)
    stats = newsGroupFile.newsGroupData.ro.statistics
    if rejectID not in stats[""]:
        for k, v in list(stats.items()):
            if k == "":
                v.append(rejectID)
            else:
                v.append(0)
    rejectCol = stats[""].index(rejectID)
    modRow = stats.get(moderatorID)
    if not modRow:
        modRow = stats[moderatorID] = len(stats[""])*[ 0 ]
    modRow[rejectCol] = modRow[rejectCol] + 1
    newsGroupFile.WriteData()
    app.Write()
AddCmd(MessageReject)

def MessageCancel(messageID, modContext):
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may cancel a message.")
    raise CmdError("Usenet message cancelling not yet implemented.")
AddCmd(MessageCancel)

def MessageDelete(messageID, modContext):
    app = serVar.app
    if modContext[0].ro.userType != "Superuser":
        raise CmdError("Only superusers may delete a message.")
    newsGroupFile = CurrentNewsgroup(modContext)
    message = newsGroupFile.ReadMessage(messageID)
    if message.ro.status != "Rejected":
        raise CmdError("May only delete rejected messages.")
    newsGroupFile.DeleteMessageFile(messageID)
AddCmd(MessageDelete)

#------------------------------------------------------------------------------
def DoCommand(cmd, args, modContext):
    if cmd != "ServerLogin" and modContext[0] == None:
        raise CmdError("Not logged in.")
    if cmd in validCmds:
        try:
            args.append(modContext)
            return validCmds[cmd](*args)
        except CmdError:
            raise
        except:
            t, v, i = sys.exc_info()
            excStr = string.join(traceback.format_exception(t, v, i), "")
            raise CmdError("%s" % excStr)
    else:
        raise CmdError("Invalid command")

#------------------------------------------------------------------------------
class AcceptHandler(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(("", serVar.app.ro.servicePort))
        self.listen(3)

    def handle_accept(self):
        sock, remAddr = self.accept()
        ClientHandler(sock, remAddr).add_channel()

#------------------------------------------------------------------------------
class ClientHandler(asyncore.dispatcher):
    def __init__(self, sock, remAddr):
        print("ClientHandler ", remAddr)
        asyncore.dispatcher.__init__(self, sock)
        self.remAddr = remAddr
        self.inBuffer = ""
        self.outBuffer = ""
        self.inLenNeeded = 4
        self.modContext = [ None ]
        self.funcState = self.ExtractCmdLen
        self.cmdFile = io.StringIO()
        self.idleTimeout = TimeNow() + serVar.app.rw.idleTimeLogout

    def handle_read(self):
        inStr = self.recv(self.inLenNeeded)
        self.inLenNeeded = self.inLenNeeded - len(inStr)
        self.inBuffer = self.inBuffer + inStr
        if not self.inLenNeeded:
            self.funcState = self.funcState()
            self.inBuffer = ""

    def ExtractCmdLen(self):
        # Reverse is struct.pack(">l", bufferLen)
        self.idleTimeout = TimeNow() + serVar.app.rw.idleTimeLogout
        serVar.updateSchedule = 1
        self.inLenNeeded = struct.unpack(">l", self.inBuffer)[0]
        return self.ExtractAndDoCmd

    def ExtractAndDoCmd(self):
        try:
            self.cmdFile.reset()
            self.cmdFile.truncate()
            self.cmdFile.write(self.inBuffer)
            self.cmdFile.seek(0)
            cmd = self.cmdFile.readline()
            cmd = cmd[:-1]  # Trim newline
            #print "Cmd: %s" % cmd
            args = pickle.load(self.cmdFile)
            #print "Args: %s" % args
            try:
                rsp = DoCommand(cmd, args, self.modContext)
            except CmdError:
                rsp = sys.exc_info()[1]
            #print "rsp=", rsp
            rspFile = io.StringIO()
            pickle.dump(rsp, rspFile, 1)
            buf = rspFile.getvalue()
            self.outBuffer = struct.pack(">l", len(buf)) + buf
            self.inLenNeeded = 4
            return self.ExtractCmdLen
        except:
            print("Something wrong in ExtractAndDoCmd:")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            traceback.print_tb(sys.exc_info()[2])
            self.handle_close()

    def readable(self):
        return self.inLenNeeded

    def writable(self):
        return self.outBuffer

    def handle_write(self):
        numSent = self.send(self.outBuffer)
        self.outBuffer = self.outBuffer[numSent:]
        if numSent < 1:
            self.handle_close()

    def handle_close(self):
        # Do logout timestamp update and flag off.
        ServerLogout(self.modContext)
        self.close()
        print("Close ", self.remAddr)

#------------------------------------------------------------------------------
def PeriodicPost(newsGroupID, messageID):
    newsGroupFile = serVar.app.newsGroupFiles.get(newsGroupID)
    if newsGroupFile:
        newsGroup = newsGroupFile.newsGroupData
        periodInfo = newsGroup.rw.periodicPosts.get(messageID)
        if periodInfo:
            try:
                msg = newsGroupFile.ReadMessage(messageID)
            except:
                # Message unreadble because it was deleted or other reason.
                # Silently remove it from the periodic posting schedule. :-(
                del newsGroup.rw.periodicPosts[messageID]
                return
            periodInfo[0] = TimeNow() + periodInfo[1]
            # Now post the message if it is in approval state.
            if msg.ro.status == "Approved":
                if newsGroup.rw.postFromServer:
                    eventRW = EventRWData("Scheduled Post")
                    rw = serVar.app.rw
                    try:
                        PostMessage(msg.ro.outHeaders, msg.ro.outTxt,
                            rw.nntpHost, rw.nntpPort, rw.nntpUser,
                            rw.nntpPassword)
                    except CmdError as errVal:
                        eventRW.eventDetail = errVal.details
                else:
                    toAddr = string.replace(newsGroupID, ".", "-") + \
                                "@moderators.isc.org"
                    msg.ro.outHeaders[("To", 0)] = toAddr
                    toAddrs = [ toAddr ]
                    txt, errMsg = EmailMessage(toAddrs, msg.ro.outHeaders,
                                    msg.ro.outTxt, serVar.app.rw.smtpHost)
                    eventRW = EventRWData("Scheduled Email", errMsg)
                # Add an appropriate event note each time.
                msg.ro.events[0:0] = [ EventData("root", eventRW) ]
                newsGroupFile.WriteMessage(msg)

#------------------------------------------------------------------------------
def IdleTimeout(clientHandler):
    if clientHandler.connected:
        clientHandler.handle_close()

#------------------------------------------------------------------------------
def Main():
    serVar.app = ServerApp()
    AcceptHandler()
    serVar.updateSchedule = 1
    while 1:
        if serVar.updateSchedule:
            serVar.updateSchedule = 0
            schedule = [ ]
            # Scan channels for activity to update idle times.
            for dispatcher in list(asyncore.socket_map.keys()):
                if isinstance(dispatcher, ClientHandler):
                    schedule.append([dispatcher.idleTimeout, IdleTimeout,
                                        (dispatcher,)])
            # Scan newsgroups and insert entries for scheduled messages.
            for grpID, newsGroupFile in list(serVar.app.newsGroupFiles.items()):
                groupRW = newsGroupFile.newsGroupData.rw
                for msgID, [evtTime, rptTime] in list(groupRW.periodicPosts.items()):
                    schedule.append([evtTime, PeriodicPost, (grpID, msgID)])
            schedule.sort()
        if schedule:
            timeout = max(schedule[0][0] - TimeNow(), 0.0)
        else:
            timeout = 3600.0
        asyncore.poll(timeout)
        # Check for scheduled events.
        # schedule = [ ] # [[eventTime, function, (args)],]
        while schedule and schedule[0][0] < TimeNow():
            serVar.updateSchedule = 1
            t, f, a = schedule[0]
            schedule = schedule[1:]
            try:
                f(*a)
            except:
                print("Something wrong in Scheduled function:")
                print(sys.exc_info()[0])
                print(sys.exc_info()[1])
                traceback.print_tb(sys.exc_info()[2])

