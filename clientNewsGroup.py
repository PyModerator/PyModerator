#
# Newsgroup management dialogue widget classes and support functions.
#

import time
import Pmw
import tkinter.messagebox
import tkinter.simpledialog
import altDialog
import cliVar
from tkinter import *
from clientInterfaces import *

def UpdateDisplayList():
    svr = ServerGet()
    if svr:
        cliVar.svr = svr
        app = cliVar.app
        newsGroupIDs = svr.ro.newsGroupIDs[:]
        newsGroupIDs.sort()
        app.UpdateModerateMenu()
        app.ShowModeratorStatus()
        app.selectNewsGroup.component("scrolledlist").setlist(newsGroupIDs)

def ManageNewsGroups():
    UpdateDisplayList()
    cliVar.app.selectNewsGroup.show()

def HandleManagedNewsGroup(buttonKey):
    app = cliVar.app
    if buttonKey == None or buttonKey == "Cancel":
        app.selectNewsGroup.withdraw()
        return
    if buttonKey == "Create":
        CreateANewsGroup()
    sels = app.selectNewsGroup.getcurselection()
    if len(sels) != 0:
        if buttonKey == "Edit":
            EditANewsGroup(sels[0])
        elif buttonKey == "Delete":
            DeleteANewsGroup(sels[0])

def CreateANewsGroup():
    app = cliVar.app
    newsGroup = NewsGroupData("", "", NewsGroupRWData())
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    app.editNewsGroupDialog.AllowID()
    app.editNewsGroupDialog.SetFields(newsGroup)
    buttonSelect = app.editNewsGroupDialog.GetInput()
    if buttonSelect == "OK":
        rsp = NewsGroupCreate(newsGroup.ro.newsGroupID, newsGroup.rw)
        if rsp == None:
            NewsGroupModerators(newsGroup.ro.newsGroupID,
                                newsGroup.ro.moderatorIDs)
            UpdateDisplayList()

def EditANewsGroup(newsGroupID):
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    app = cliVar.app
    newsGroup = NewsGroupGet(newsGroupID)
    if newsGroup == None:
        return
    app.editNewsGroupDialog.DisallowID()
    app.editNewsGroupDialog.SetFields(newsGroup)
    buttonSelect = app.editNewsGroupDialog.GetInput()
    if buttonSelect == "OK":
        rsp = NewsGroupUpdate(newsGroupID, newsGroup.rw)
        if rsp == None:
            # Basic newsgroup information updated ok, now do the moderators.
            NewsGroupModerators(newsGroup.ro.newsGroupID,
                                newsGroup.ro.moderatorIDs)
            UpdateDisplayList()

def DeleteANewsGroup(newsGroupID):
    button = tkinter.messagebox.askquestion("Delete Newsgroup %s" % newsGroupID,
                "WARNING! You are about to delete the newsgroup %s.\n"
                "Are you sure you want to do that??" % newsGroupID)
    if button != "yes":
        tkinter.messagebox.showinfo("Delete Aborted", "Deletion of %s aborted." %
                                newsGroupID)
        return
    button = tkinter.messagebox.askquestion("Delete Newsgroup %s" % newsGroupID,
                "Are you REALLY sure you want to do that??")
    if button != "yes":
        tkinter.messagebox.showinfo("Delete Aborted", "Deletion of %s aborted." %
                                newsGroupID)
    else:
        NewsGroupDelete(newsGroupID)
        UpdateDisplayList()

class EditNewsGroupDialog(altDialog.AltDialog):
    def SetFields(self, newsGroup):
        if self.inUse:
            return
        self.newsGroup = newsGroup
        rw = newsGroup.rw
        ro = newsGroup.ro
        self.newsGroupID.setentry(ro.newsGroupID)
        self.popHost.setentry(rw.popHost)
        self.popPort.setentry(str(rw.popPort))
        self.popUserID.setentry(rw.popUserID)
        self.popPassword.setentry(rw.popPassword)
        self.allowCrossPosts.invoke(rw.allowCrossPosts)
        self.roundRobinAssign.invoke(rw.roundRobinAssign)
        self.quotingYellow.setentry(str(rw.quotingYellow))
        self.quotingRed.setentry(str(rw.quotingRed))
        self.postFromServer.invoke(rw.postFromServer)
        self.createTime.setentry(LocalTimeRg(ro.createTime))
        self.creatorModeratorID.setentry(ro.creatorModeratorID)
        self.moderators.deleteall()
        for moderatorID in list(cliVar.svr.ro.moderators.keys()):
            self.moderators.add(moderatorID)
            if moderatorID in ro.moderatorIDs:
                self.moderators.invoke(moderatorID)

    def DisallowID(self):
        self.newsGroupID.component("entry")["state"] = DISABLED

    def AllowID(self):
        self.newsGroupID.component("entry")["state"] = NORMAL

    def Body(self, master):
        self.title("Manage Newsgroup")
        self.newsGroupID = Pmw.EntryField(master, labelpos=W,
                        label_text = "Newsgroup ID :")
        self.popHost = Pmw.EntryField(master, labelpos=W,
                        label_text = "POP Host :")
        self.popPort = Pmw.EntryField(master, labelpos=W,
                        label_text = "POP Port :", validate = "numeric")
        self.popUserID = Pmw.EntryField(master, labelpos=W,
                        label_text = "POP User ID :")
        self.popPassword = Pmw.EntryField(master, labelpos=W,
                        label_text = "POP Password :")
        self.popPassword.component("entry")["show"] = "*"
        self.allowCrossPosts = w = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Allow Cross Posts :")
        w.add("No")
        w.add("Yes")
        self.roundRobinAssign = w = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Round Robin Assignment :")
        w.add("No")
        w.add("Yes")
        self.quotingYellow = Pmw.EntryField(master, labelpos=W,
                        label_text = "New Material Yellow % :",
                        validate = "numeric")
        self.quotingRed = Pmw.EntryField(master, labelpos=W,
                        label_text = "New Material Red % :",
                        validate = "numeric")
        self.postFromServer = w = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Post From Server :")
        w.add("No")
        w.add("Yes")
        self.createTime = Pmw.EntryField(master, labelpos=W,
                        label_text = "Create Time :", entry_state = DISABLED)
        self.creatorModeratorID = Pmw.EntryField(master, labelpos=W,
                        label_text = "Creator ID :", entry_state = DISABLED)
        self.moderators = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Moderators :", orient = VERTICAL,
                        selectmode = MULTIPLE)

        widgets = (self.newsGroupID, self.popHost, self.popPort,
                    self.popUserID, self.popPassword, self.allowCrossPosts,
                    self.roundRobinAssign, self.quotingYellow, self.quotingRed,
                    self.postFromServer, self.createTime,
                    self.creatorModeratorID, self.moderators)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.newsGroupID.component("entry")

    def Apply(self):
        rw = self.newsGroup.rw
        ro = self.newsGroup.ro
        ro.newsGroupID = self.newsGroupID.get().strip()
        rw.popHost = self.popHost.get().strip()
        rw.popPort = int(self.popPort.get().strip())
        rw.popUserID = self.popUserID.get().strip()
        rw.popPassword = self.popPassword.get()
        w = self.allowCrossPosts
        rw.allowCrossPosts = w.index(w.getcurselection())
        w = self.roundRobinAssign
        rw.roundRobinAssign = w.index(w.getcurselection())
        rw.quotingYellow = int(self.quotingYellow.get().strip())
        rw.quotingRed = int(self.quotingRed.get().strip())
        rw.popHost = self.popHost.get().strip()
        w = self.postFromServer
        rw.postFromServer = w.index(w.getcurselection())
        ro.moderatorIDs = self.moderators.getcurselection()

