#
# This has the Main function which starts the user interface and the main
# application class (PyModeratorClient). It also contains a lot of
# miscellaneous dialogue support functions that probably should go into other
# modules.
#

import os
import sys
import time
import socket
import AppShell
import pickle
import Pmw
import tkinter.messagebox
import tkinter.simpledialog
import altDialog
import cliVar
import io
import string
from tkinter import *
from clientInterfaces import *
from clientLogin import *
from clientNewsGroup import *
from clientModerator import *
from clientRejection import *
from clientMsgLists import *
from clientMsgView import *
from clientEMail import *
from clientSearchArchive import *
from clientScheduleMsgs import *

class CachedData:
    def __init__(self):
        self.loginID = ""
        self.serviceHost = "127.0.0.1"
        self.servicePort = 11556
        self.nntpHost = ""
        self.nntpPort = 119
        self.nntpUser = ""
        self.nntpPassword = ""
        self.smtpHost = ""
        self.ballonState = "both"

class PyModeratorClient(AppShell.AppShell):
    appversion = cliVar.appVersion
    appname = "PyModerator"
    copyright = "Copyright 2001 Lugoj Incorporated.\n" \
        "Pmw copyrighted 2001 by Telstra Corporation Limited, Australia.\n" \
        "AppShell copyrighted 2000 by Doug Hellmann & John E. Grayson."
    contactname = "James Logajan"
    contactemail = "JamesL@Lugoj.com"
    usecommandarea = 0
    frameWidth = 1020
    frameHeight = 760

    def ReadCache(self):
        self.dataFile.seek(0)
        self.cache = pickle.load(self.dataFile)
        if not hasattr(self.cache, "ballonState"):
            self.cache.ballonState = "both"

    def WriteCache(self):
        self.dataFile.seek(0)
        pickle.dump(self.cache, self.dataFile, 1)
        self.dataFile.flush()

    def appInit(self):
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.password = ""
        self.svrClockFaster = 0
        self.fn = "%s/client.cfg" % cliVar.path
        if not os.path.exists(cliVar.path):
            os.mkdir(cliVar.path)
        try:
            self.dataFile = open(self.fn, "rb+")
            self.ReadCache()
        except IOError:
            self.dataFile = open(self.fn, "wb+")
            self.cache = CachedData()
            self.WriteCache()
        self.rejectButtons = [ ]
        self.modInfoW = [ ]

    def createInterface(self):
        AppShell.AppShell.createInterface(self)
        self.root.minsize(width=300, height=300)
        self.balloon().configure(state = self.cache.ballonState)
        w = self.menuBar
        w.addmenuitem("Session", "command",
                "Connect and login to server.", label = "Login...",
                command = self.Login)
        w.addmenuitem("Session", "separator")
        w.addmenuitem("Session", "command",
                "Check for new posts and refresh display from server.",
                label = "Refresh from Server", command = RefreshAll)
        w.addmenuitem("Session", "separator")
        w.addmenuitem("Session", "command",
                "Logout and disconnect from server.", label = "Logout",
                command = self.Logout)
        w.addmenuitem("Session", "command",
                "Quit %s." % self.appname, label = "Quit", command = self.quit)
        w.addmenu("Manage", "Editing commands.")
        w.addmenuitem("Manage", "command",
                "Edit login information.", label = "Login Fields...",
                command = self.EditLoginDialog)
        w.addmenuitem("Manage", "command",
                "Edit server's connect information. (Superuser)",
                label = "Server Info...",
                command = self.EditServerDialog)
        w.addmenuitem("Manage", "command",
                "Change moderator's password.",
                label = "Change Password...",
                command = self.ChangePasswordDialog)
        w.addmenuitem("Manage", "command",
                "Edit, create, and delete newsgroups.", label="Newsgroups...",
                command = ManageNewsGroups)
        w.addmenuitem("Manage", "command",
                "Edit, create, and delete moderators.", label = "Moderators...",
                command = ManageModerators)
        w.addmenuitem("Manage", "command",
                "Tell server to update list of valid newsgroups. (Long!)",
                label = "Update Valid Groups...",
                command = self.ConfirmValidGroupsUpdate)
        w.addmenu("Message", "Manage messages in the current newsgroup.")
        w.addmenuitem("Message", "command",
                "Display newsgroup approve/reject statistics.",
                label = "Statistics...", command = ShowStatistics)
        w.addmenuitem("Message", "command",
                "Edit, create, and delete newsgroup rejection types.",
                label = "Rejection Types...", command = ManageRejections)
        w.addmenuitem("Message", "command",
                "Manage messages that should be periodically reposted.",
                label = "Periodic Posts...", command = PeriodicPosts)
        w.addmenuitem("Message", "separator")
        w.addmenuitem("Message", "command",
                "Delete currently selected message.",
                label = "Delete...", command = DeleteMessage)
        w.addmenu("Moderate", "Select newsgroup to moderate.")
        w.addmenuitem("Moderate", "command",
                "", label = "none",
                command = lambda : ModerateNewsGroup("none"))
        self.editLoginData = EditLoginData(self.root)
        self.loginDialog = LoginDialog(self.root)
        self.editServerData = EditServerData(self.root)
        self.changePassword = ChangePassword(self.root)
        self.emailDialog = EMailDialog(self.root)
        self.selectNewsGroup = Pmw.SelectionDialog(self.root,
                        title = "Select Newsgroup to Manage",
                        buttons = ("Edit", "Create", "Delete", "Cancel"),
                        defaultbutton = "Edit",
                        command = HandleManagedNewsGroup)
        self.selectNewsGroup.withdraw()
        self.selectNewsGroup.geometry("+%d+%d" % (self.root.winfo_rootx() + 50,
                                                self.root.winfo_rooty() + 50))
        self.statDisplay = Pmw.TextDialog(self.root,
                        title = "Message Approve/Reject Statistics",
                        buttons = ("OK",))
        self.statDisplay.withdraw()
        self.statDisplay.geometry("+%d+%d" % (self.root.winfo_rootx() + 50,
                                                self.root.winfo_rooty() + 50))
        self.editNewsGroupDialog = EditNewsGroupDialog(self.root)
        self.selectModerator = Pmw.SelectionDialog(self.root,
                        title = "Select Moderator to Manage",
                        buttons = ("Edit", "Create", "Delete", "Cancel"),
                        defaultbutton = "Edit",
                        command = HandleManagedModerator)
        self.selectModerator.withdraw()
        self.selectModerator.geometry("+%d+%d" % (self.root.winfo_rootx() + 50,
                                                self.root.winfo_rooty() + 50))
        self.editModeratorDialog = EditModeratorDialog(self.root)
        self.selectRejection = Pmw.SelectionDialog(self.root,
                        title = "Select Rejection to Manage",
                        buttons = ("Edit", "Create", "Delete", "Cancel"),
                        defaultbutton = "Edit",
                        command = HandleManagedRejection)
        self.selectRejection.withdraw()
        self.selectRejection.geometry("+%d+%d" % (self.root.winfo_rootx() + 50,
                                                self.root.winfo_rooty() + 50))
        self.editRejectionDialog = EditRejectionDialog(self.root)
        self.selectReassign = Pmw.SelectionDialog(self.root,
                        title = "Reassign Message to Selected Moderator",
                        buttons = ("OK", "Cancel"),
                        defaultbutton = "OK",
                        command = HandleReassignment)
        self.selectReassign.withdraw()
        self.selectReassign.geometry("+%d+%d" % (self.root.winfo_rootx() + 50,
                                                self.root.winfo_rooty() + 50))
        self.searchDialog = SearchDialog(self.root)
        self.scheduleDialog = ScheduleDialog(self.root)
        self.eventDetail = Pmw.TextDialog(self.root,
                                title = "Enter Event Detail, If Any",
                                scrolledtext_text_wrap = WORD,
                                buttons = ("OK", "Cancel"))
        self.eventDetail.withdraw()
        self.eventDetail.geometry("+%d+%d" % (self.root.winfo_rootx() + 50,
                                                self.root.winfo_rooty() + 50))
        self.mainView = Pmw.ScrolledFrame(self.interior(),
                                horizflex = "expand",
                                vertflex = "expand")
        self.mainView.pack(fill = BOTH, expand = 1)
        mainFrame = self.mainView.interior()
        self.bframe = Frame(mainFrame, relief = GROOVE, borderwidth = 4)
        self.bframe.pack(side = TOP, fill = X)
        self.cframe = Frame(mainFrame, relief = GROOVE, borderwidth = 4)
        self.cframe.pack(side = TOP, fill = X)
        self.modInfo = Frame(mainFrame)
        self.modInfo.pack(side = TOP)
        self.aframe = Frame(mainFrame)
        self.aframe.pack(side = TOP, fill = BOTH, expand = 1)
        self.messageView = MessageView(self.aframe)
        self.messageLists = MessageLists(self.aframe, self.messageView)
        self.messageLists.pack(side = LEFT, fill = BOTH, expand = 1)
        self.messageView.pack(side = LEFT, fill = BOTH, expand = 1)
        Button(self.bframe, text = "Approve", command = DoApprove,
                    width = 14).pack(side = LEFT, padx = 2, pady = 2)
        Button(self.bframe, text = "Limbo", command = DoLimbo,
                    width = 14).pack(side = LEFT, padx = 2, pady = 2)
        Button(self.bframe, text = "Reassign", command = DoReassign,
                    width = 14).pack(side = LEFT, padx = 2, pady = 2)
        Button(self.bframe, text = "Add Event Note", command = DoAddEventNote,
                    width = 14).pack(side = LEFT, padx = 2, pady = 2)
        Button(self.bframe, text = "E-Mail Poster", command = DoEmailPoster,
                    width = 14).pack(side = LEFT, padx = 2, pady = 2)
        Button(self.bframe, text = "Search Archive", command = DoSearch,
                    width = 14).pack(side = LEFT, padx = 2, pady = 2)

    def ConfirmValidGroupsUpdate(self):
        button = tkinter.messagebox.askquestion("Confirm Update Request",
                "Updating the list of all possible newsgroups will\n"
                "take many minutes. Are you sure you want to do this?",
                default = "no")
        if button == "yes":
            ServerUpdateValidGroups()

    def EditLoginDialog(self):
        self.editLoginData.SetFields()
        self.editLoginData.GetInput()

    def EditServerDialog(self):
        self.editServerData.SetFields()
        self.editServerData.GetInput()

    def ChangePasswordDialog(self):
        self.changePassword.SetFields()
        self.changePassword.GetInput()

    def Login(self):
        if cliVar.sockFile == None:
            failReason = self.ConnectToServer()
            if failReason:
                Oops("Unable to connect to server '%s': %s." %
                            (self.cache.serviceHost, failReason))
                return
        self.loginDialog.SetFields()
        buttonLabel = self.loginDialog.GetInput()
        if buttonLabel == "OK":
            rsp =  ServerLogin(self.cache.loginID, self.password)
            if rsp == None:
                Oops("Invalid login.")
            else:
                self.svrClockFaster = rsp.ro.lastLogin - TimeNow()
                cliVar.thisModerator = rsp
                cliVar.thisModeratorID = rsp.ro.moderatorID
                RefreshAll()

    def UpdateModerateMenu(self):
        self.menuBar.deletemenuitems("Moderate", 0, 99)
        if cliVar.thisModeratorID:
            cliVar.thisModerator = ModeratorGet(cliVar.thisModeratorID)
            newsGroupIDs = cliVar.thisModerator.ro.newsGroupIDs
        else:
            cliVar.thisModerator = None
            newsGroupIDs = [ ]
        for newsGroupID in newsGroupIDs + [ "none" ]:
            self.menuBar.addmenuitem("Moderate", "command",
                "", label = newsGroupID,
                command =
                    lambda id = newsGroupID : ModerateNewsGroup(id))
        self.root.title("%s   %s" % (self.appname, cliVar.currentNewsGroupID))

    def Logout(self):
        ServerLogout()
        cliVar.sockFile = None
        cliVar.thisModeratorID = ""
        self.UpdateModerateMenu()
        ModerateNewsGroup(None)

    def ConnectToServer(self):
        self.busyStart()
        try:
            sockFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockFd.connect((self.cache.serviceHost, self.cache.servicePort))
            cliVar.sockFile = sockFd.makefile("rwb")
        except:
            self.busyEnd()
            return sys.exc_info()[1]
        self.busyEnd()
        return None

    def ShowModeratorStatus(self):
        for w in self.modInfoW:
            w.destroy()
        self.modInfoW = [ ]
        if cliVar.currentNewsGroup:
            refTime = TimeNow() + self.svrClockFaster
            for moderatorID in cliVar.currentNewsGroup.ro.moderatorIDs:
                moderator = cliVar.svr.ro.moderators.get(moderatorID)
                if moderator:
                    if moderator.ro.loggedIn:
                        fgcolor = "brown"
                        if moderator.ro.lastLogin:
                            timeSince = refTime - moderator.ro.lastLogin
                        else:
                            timeSince = 0
                        inStat = "on %.1f hrs ago." % (timeSince/3600.0)
                    else:
                        if moderator.ro.lastLogout:
                            fgcolor = "black"
                            timeSince = refTime - moderator.ro.lastLogout
                            inStat = "left %.1f hrs ago." % (timeSince/3600.0)
                        else:
                            fgcolor = "green"
                            inStat = "never on."
                            timeSince = 0
                    if moderator.rw.vacation:
                        vac = " (Vac)"
                    else:
                        vac = ""
                    w = Label(self.modInfo, relief = RIDGE, fg = fgcolor,
                                text = "%s: %s %s%s" %
                                (moderator.ro.userType[0], moderatorID,
                                inStat, vac))
                    self.modInfoW.append(w)
                    w.pack(side = LEFT, expand = 1, padx = 5)
        self.update_idletasks()

class EditServerData(altDialog.AltDialog):
    def SetFields(self):
        if self.inUse:
            return
        rw = cliVar.svr.rw
        self.nntpHost.setentry(rw.nntpHost)
        self.nntpPort.setentry(str(rw.nntpPort))
        self.nntpUser.setentry(rw.nntpUser)
        self.nntpPassword.setentry(rw.nntpPassword)
        self.smtpHost.setentry(rw.smtpHost)
        self.idleTimeLogout.setentry(str(rw.idleTimeLogout))

    def Body(self, master):
        self.title("Edit Server's Connection Information")
        self.nntpHost = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP Host :")
        self.nntpPort = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP Port :", validate = "numeric")
        self.nntpUser = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP User :")
        self.nntpPassword = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP Password :")
        self.smtpHost = Pmw.EntryField(master, labelpos=W,
                            label_text = "SMTP Host :")
        self.idleTimeLogout = Pmw.EntryField(master, labelpos=W,
                            label_text = "Idle Timeout (secs) :",
                            validate = "numeric")
        widgets = (self.nntpHost, self.nntpPort, self.nntpUser,
                    self.nntpPassword, self.smtpHost, self.idleTimeLogout)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.nntpHost

    def Validate(self):
        tmpRW = ServerRWData()
        tmpRW.nntpHost = self.nntpHost.get().strip()
        tmpRW.nntpPort = int(self.nntpPort.get().strip())
        tmpRW.nntpUser = self.nntpUser.get().strip()
        tmpRW.nntpPassword = self.nntpPassword.get()
        tmpRW.smtpHost = self.smtpHost.get().strip()
        tmpRW.idleTimeLogout = int(self.idleTimeLogout.get().strip())
        if ServerUpdate(tmpRW) == None:
            cliVar.svr.rw = tmpRW
            return 1
        return 0

def ShowStatistics():
    app = cliVar.app
    if cliVar.currentNewsGroup:
        stats = cliVar.currentNewsGroup.ro.statistics
        colNames = stats[""][:] + ["Totals"]
        colWidths = list(map(len, colNames))
        numCols = len(colNames)
        modNames = list(stats.keys())
        modWidth = max(list(map(len, modNames + ["Totals"]))) + 1
        hdr = modWidth*" " + string.join(colNames, " ") + "\n"
        dmsg = hdr
        rows = list(stats.items())
        rows.sort()
        colTotals = numCols*[0]
        for modID, columns in rows:
            columns = columns[:] + [0]
            if modID != "":
                dmsg = "%s%-*s" % (dmsg, modWidth, modID)
                for jdx in range(numCols - 1):
                    columns[-1] = columns[-1] + columns[jdx]
                for jdx in range(numCols):
                    colTotals[jdx] = colTotals[jdx] + columns[jdx]
                    dmsg = dmsg + "%*d " % (colWidths[jdx], columns[jdx])
                dmsg = dmsg + "\n"
        dmsg = "\n%s%*s" % (dmsg, modWidth, "Totals")
        for jdx in range(numCols):
            dmsg = dmsg + "%*d " % (colWidths[jdx], colTotals[jdx])
        scrolledtext = app.statDisplay.component("scrolledtext")
        scrolledtext.settext(dmsg)
        scrolledtext.component("text").configure(width = len(hdr))
        app.statDisplay.show()

def DeleteMessage():
    app = cliVar.app
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        moderator = cliVar.thisModerator
        msgID = msg.ro.messageID
        if not tkinter.messagebox.askokcancel("Confirm Deletion",
                                        "Delete message %d?" % msgID):
            return
        MessageDelete(msgID)

def RefreshAll():
    if cliVar.thisModerator:
        ModerateNewsGroup(cliVar.thisModerator.ro.currentNewsGroupID)
    else:
        ModerateNewsGroup(None)

def ModerateNewsGroup(newsGroupID):
    if cliVar.sockFile != None:
        cliVar.svr = ServerGet()
    if not newsGroupID or newsGroupID == "none":
        newsGroupID = ""
    cliVar.currentNewsGroupID = newsGroupID
    if newsGroupID:
        if ServerSetNewsGroup(newsGroupID) == 1:
            # Update main display.
            NewsGroupGetIncomingPosts(cliVar.currentNewsGroupID)
            cliVar.currentNewsGroup = NewsGroupGet(newsGroupID)
    else:
        cliVar.currentNewsGroup = None
    cliVar.app.UpdateModerateMenu()
    cliVar.app.ShowModeratorStatus()
    cliVar.app.messageLists.UpdateView()
    UpdateRejectionDisplayList()
    cliVar.app.update_idletasks()

def DoApprove():
    app = cliVar.app
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        moderator = cliVar.thisModerator
        if not moderator:
            return Oops("Current moderator not valid!")
        if moderator.ro.userType == "Guest":
            return Oops("Guests may not approve messages.")
        msgID = msg.ro.messageID
        if msg.ro.status in ["Rejected", "Approved"]:
            return Oops("Message '%d' already processed." % msgID)
        if not tkinter.messagebox.askokcancel("Confirm Approval",
                                        "Approve message %d?" % msgID):
            return
        outHeaders = msg.ro.outHeaders
        outHeaders[("X-psw", 0)] = "PyModerator " + cliVar.appVersion
        name = fromAddress = ""
        fromAddress = moderator.rw.fromAddress
        if not fromAddress:
            fromAddress = cliVar.thisModeratorID
        outHeaders[("Approved", 0)] = fromAddress
        outTxt = string.join(WordWrap(string.split(msg.ro.outTxt, "\n")), "\n")
        if not cliVar.currentNewsGroup.rw.postFromServer:
            usr = app.cache
            try:
                PostMessage(outHeaders, outTxt, usr.nntpHost, usr.nntpPort,
                            usr.nntpUser, usr.nntpPassword)
            except CmdError as err:
                return Oops(err)
        MessageApprove(msgID, outTxt, outHeaders, "")
        cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
        app.messageLists.UpdateView()

def HandleLimboDetail(button):
    app = cliVar.app
    app.eventDetail.withdraw()
    if button != "OK":
        return
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        msgID = msg.ro.messageID
        LimboTheMessage(msgID, app.eventDetail.component("scrolledtext").get())
        cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
        app.messageLists.UpdateView()

def DoLimbo():
    app = cliVar.app
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        msgID = msg.ro.messageID
        app.eventDetail.configure(command = HandleLimboDetail)
        app.eventDetail.component("text").focus_set()
        app.eventDetail.show()

def DoReassign():
    app = cliVar.app
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        msgID = msg.ro.messageID
        moderatorIDs = list(cliVar.svr.ro.moderators.keys())
        moderatorIDs.sort()
        app.selectReassign.component("scrolledlist").setlist(moderatorIDs)
        app.selectReassign.show()

def HandleReassignment(buttonKey):
    app = cliVar.app
    if buttonKey == None or buttonKey == "Cancel":
        app.selectReassign.withdraw()
        return
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        msgID = msg.ro.messageID
        sels = app.selectReassign.getcurselection()
        if len(sels) != 0:
            MessageReassign(msgID, sels[0])
            cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
            app.messageLists.UpdateView()

def HandleEventNote(button):
    app = cliVar.app
    app.eventDetail.withdraw()
    if button != "OK":
        return
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        msgID = msg.ro.messageID
        detail = app.eventDetail.component("scrolledtext").get()
        eventRW = EventRWData("Note", detail)
        MessageAddEvent(msgID, eventRW)
        cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
        app.messageLists.UpdateView()

def DoAddEventNote():
    app = cliVar.app
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        msgID = msg.ro.messageID
        app.eventDetail.configure(command = HandleEventNote)
        app.eventDetail.component("text").focus_set()
        app.eventDetail.show()

def DoEmailPoster():
    app = cliVar.app
    msg = app.messageView.GetMessage()
    if msg and cliVar.currentNewsGroup:
        msgID = msg.ro.messageID
        detail = SendEMailReply(msg, "")
        if detail != None:
            eventRW = EventRWData("Email", detail)
            MessageAddEvent(msgID, eventRW)
            cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
            app.messageLists.UpdateView()

def Main():
    cliVar.app = PyModeratorClient(balloon_state='both')
    cliVar.app.run()

