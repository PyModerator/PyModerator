#
# This are the client side functions that communicate requests to the server.
#

import pickle
import tkinter.messagebox
import cliVar
import struct
import io
from commonDefs import *

#------------------------------------------------------------------------------
def Oops(err):
    if isinstance(err, CmdError):
        msg = err.details
    else:
        msg = err
    tkinter.messagebox.showerror("Error", msg)
    return None

cmdFile = io.BytesIO()

#------------------------------------------------------------------------------
def ReadSock(num):
    buf = bytearray()
    while len(buf) < num:
        inBytes = cliVar.sockFile.read(num - len(buf))
        if len(inBytes) < 1:
            raise IOError
        buf = buf + inBytes
    return buf

#------------------------------------------------------------------------------
def DoCommand(cmd, args):
    global cmdFile
    #print "DoCommand %s" % (cmd, )
    #print "DoCommand %s:%s" % (cmd, args)
    if cliVar.sockFile == None:
        return Oops("Not connected to server!")
    cliVar.app.busyStart()
    try:
        cmdFile.seek(0)
        cmdFile.truncate()
        cmd = cmd + "\n"
        cmdFile.write(cmd.encode(encoding='utf-8'))
        pickle.dump(args, cmdFile, 1)
        cmdBuf = cmdFile.getvalue()
        cmdLen = struct.pack(">l", len(cmdBuf))
        cliVar.sockFile.write(cmdLen)
        cliVar.sockFile.write(cmdBuf)
        cliVar.sockFile.flush()
        # Ignore the rspLen for now. May use it later for async operation.
        rspLen = struct.unpack(">l", ReadSock(4))[0]
        rsp = pickle.load(cliVar.sockFile)
    except IOError:
        cliVar.sockFile = None
        cliVar.app.busyEnd()
        return Oops("Server disconnected from us!")
    cliVar.app.busyEnd()
    #print "Response:%s" % repr(rsp)
    if isinstance(rsp, CmdError):
        return Oops(rsp)
    return rsp

#------------------------------------------------------------------------------
def ServerLogin(moderatorID, password):
    return DoCommand("ServerLogin", [moderatorID, password])

def ServerSetNewsGroup(newsGroupID):
    return DoCommand("ServerSetNewsGroup", [newsGroupID])

def ServerLogout():
    return DoCommand("ServerLogout", [])

def ServerUpdate(serverRW):
    return DoCommand("ServerUpdate", [serverRW])

def ServerGet():
    return DoCommand("ServerGet", [])

def ServerUpdateValidGroups():
    return DoCommand("ServerUpdateValidGroups", [])

#------------------------------------------------------------------------------
def ModeratorCreate(moderatorID, password, moderatorRW):
    return DoCommand("ModeratorCreate", [moderatorID, password, moderatorRW])

def ModeratorList():
    return DoCommand("ModeratorList", [])

def ModeratorGet(moderatorID):
    return DoCommand("ModeratorGet", [moderatorID])

def ModeratorUpdate(moderatorID, moderatorRW):
    return DoCommand("ModeratorUpdate", [moderatorID, moderatorRW])

def ModeratorChangePW(moderatorID, newPW):
    return DoCommand("ModeratorChangePW", [moderatorID, newPW])

def ModeratorChangeType(moderatorID, userType):
    return DoCommand("ModeratorChangeType", [moderatorID, userType])

def ModeratorDelete(moderatorID):
    return DoCommand("ModeratorDelete", [moderatorID])

#------------------------------------------------------------------------------
def MessageCreate(messageRW):
    return DoCommand("MessageCreate", [messageRW])

def MessageSummaries(messageIDs):
    return DoCommand("MessageSummaries", [messageIDs])

def MessageGet(messageID):
    return DoCommand("MessageGet", [messageID])

def MessageLock(messageID):
    return DoCommand("MessageLock", [messageID])

def MessageUnLock(messageID):
    return DoCommand("MessageUnLock", [messageID])

def MessageReassign(messageID, assignTo):
    return DoCommand("MessageReassign", [messageID, assignTo])

def MessageAddEvent(messageID, eventRW):
    return DoCommand("MessageAddEvent", [messageID, eventRW])

def MessageApprove(messageID, outTxt, outHeaders, details):
    return DoCommand("MessageApprove", [messageID, outTxt, outHeaders, details])

def MessageReject(messageID, rejectID, details):
    return DoCommand("MessageReject", [messageID, rejectID, details])

def MessageCancel(messageID):
    return DoCommand("MessageCancel", [messageID])

def MessageDelete(messageID):
    return DoCommand("MessageDelete", [messageID])

#------------------------------------------------------------------------------
def RejectionCreate(rejectionID, rejectionRW):
    return DoCommand("RejectionCreate", [rejectionID, rejectionRW])

def RejectionList():
    return DoCommand("RejectionList", [])

def RejectionGet(rejectionID):
    return DoCommand("RejectionGet", [rejectionID])

def RejectionUpdate(rejectionID, rejectionRW):
    return DoCommand("RejectionUpdate", [rejectionID, rejectionRW])

def RejectionDelete(rejectionID):
    return DoCommand("RejectionDelete", [rejectionID])

#------------------------------------------------------------------------------
def ReviewListMessages():
    return DoCommand("ReviewListMessages", [])

def LimboListMessages():
    return DoCommand("LimboListMessages", [])

def LimboTheMessage(messageID, detail):
    return DoCommand("LimboTheMessage", [messageID, detail])

def SearchArchive(searchExp, ignoreCase, itemNames):
    return DoCommand("SearchArchive", [searchExp, ignoreCase, itemNames])

#------------------------------------------------------------------------------
def NewsGroupCreate(newsGroupID, newsGroupRW):
    return DoCommand("NewsGroupCreate", [newsGroupID, newsGroupRW])

def NewsGroupGet(newsGroupID):
    return DoCommand("NewsGroupGet", [newsGroupID])

def NewsGroupList():
    return DoCommand("NewsGroupList", [])

def NewsGroupUpdate(newsGroupID, newsGroupRW):
    return DoCommand("NewsGroupUpdate", [newsGroupID, newsGroupRW])

def NewsGroupDelete(newsGroupID):
    return DoCommand("NewsGroupDelete", [newsGroupID])

def NewsGroupGetIncomingPosts(newsGroupID):
    return DoCommand("NewsGroupGetIncomingPosts", [newsGroupID])

def NewsGroupModerators(newsGroupID, moderatorIDs):
    return DoCommand("NewsGroupModerators", [newsGroupID, moderatorIDs])

def AddModeratorToNewsGroup(moderatorID, newsGroupID):
    return DoCommand("AddModeratorToNewsGroup", [moderatorID, newsGroupID])

def DelModeratorFromNewsGroup(moderatorID, newsGroupID):
    return DoCommand("DelModeratorFromNewsGroup", [moderatorID, newsGroupID])

