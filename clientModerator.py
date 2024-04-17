#
# Moderator management dialogue widget classes and support functions.
#

import time
import Pmw
import tkMessageBox
import tkSimpleDialog
import altDialog
import cliVar
import string
from Tkinter import *
from clientInterfaces import *

sstrip = string.strip

def UpdateDisplayList():
    svr = ServerGet()
    if svr:
        cliVar.svr = svr
        app = cliVar.app
        moderatorIDs = svr.ro.moderators.keys()
        moderatorIDs.sort()
        app.UpdateModerateMenu()
        app.ShowModeratorStatus()
        app.selectModerator.component("scrolledlist").setlist(moderatorIDs)

def ManageModerators():
    UpdateDisplayList()
    cliVar.app.selectModerator.show()

def HandleManagedModerator(buttonKey):
    app = cliVar.app
    if buttonKey == None or buttonKey == "Cancel":
        app.selectModerator.withdraw()
        return
    if buttonKey == "Create":
        CreateAModerator()
    sels = app.selectModerator.getcurselection()
    if len(sels) <> 0:
        if buttonKey == "Edit":
            EditAModerator(sels[0])
        elif buttonKey == "Delete":
            DeleteAModerator(sels[0])

def CreateAModerator():
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    app = cliVar.app
    moderator = ModeratorData("", ModeratorRWData())
    app.editModeratorDialog.AllowID()
    app.editModeratorDialog.SetFields(moderator)
    buttonSelect = app.editModeratorDialog.GetInput()
    if buttonSelect == "OK":
        moderatorID = moderator.ro.moderatorID
        rsp = ModeratorCreate(moderatorID, "", moderator.rw)
        if rsp == None:
            for newsGroupID in moderator.ro.newsGroupIDs:
                AddModeratorToNewsGroup(moderatorID, newsGroupID)
            UpdateDisplayList()

def EditAModerator(moderatorID):
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    app = cliVar.app
    moderator = cliVar.svr.ro.moderators.get(moderatorID)
    if moderator == None:
        Oops("Invalid selection!")
        return
    app.editModeratorDialog.DisallowID()
    app.editModeratorDialog.SetFields(moderator)
    olduserType = moderator.ro.userType
    oldNewsGroupIDs = moderator.ro.newsGroupIDs[:]
    oldNewsGroupIDs.sort()
    buttonSelect = app.editModeratorDialog.GetInput()
    if buttonSelect == "OK":
        rsp = ModeratorUpdate(moderatorID, moderator.rw)
        if rsp == None:
            newNewsGroupIDs = list(moderator.ro.newsGroupIDs)
            newNewsGroupIDs.sort()
            if oldNewsGroupIDs <> newNewsGroupIDs:
                for newsGroupID in cliVar.svr.ro.newsGroupIDs:
                    if newsGroupID in oldNewsGroupIDs:
                        if newsGroupID not in newNewsGroupIDs:
                            DelModeratorFromNewsGroup(moderatorID, newsGroupID)
                    elif newsGroupID in newNewsGroupIDs:
                        AddModeratorToNewsGroup(moderatorID, newsGroupID)
            if olduserType <> moderator.ro.userType:
                ModeratorChangeType(moderatorID, moderator.ro.userType)
            UpdateDisplayList()

def DeleteAModerator(moderatorID):
    button = tkMessageBox.askquestion("Delete Moderator %s" % moderatorID,
                "WARNING!\n"
                "You are about to delete moderator %s.\n"
                "Are you sure you want to do that??" % moderatorID)
    if button <> "yes":
        tkMessageBox.showinfo("Delete Aborted", "Deletion of %s aborted." %
                                moderatorID)
        return
    else:
        ModeratorDelete(moderatorID)
        UpdateDisplayList()

class EditModeratorDialog(altDialog.AltDialog):
    def SetFields(self, moderator):
        if self.inUse:
            return
        self.moderator = moderator
        rw = moderator.rw
        ro = moderator.ro
        self.moderatorID.setentry(ro.moderatorID)
        self.fromAddress.setentry(rw.fromAddress)
        self.name.setentry(rw.name)
        self.vacation.invoke(rw.vacation)
        self.userType.invoke(ro.userType)
        self.createTime.setentry(LocalTimeRg(ro.createTime))
        self.lastLogin.setentry(LocalTimeRg(ro.lastLogin))
        self.lastLogout.setentry(LocalTimeRg(ro.lastLogout))
        self.newsGroupIDs.deleteall()
        for newsGroupID in cliVar.svr.ro.newsGroupIDs:
            self.newsGroupIDs.add(newsGroupID)
            if newsGroupID in ro.newsGroupIDs:
                self.newsGroupIDs.invoke(newsGroupID)

    def DisallowID(self):
        self.moderatorID.component("entry")["state"] = DISABLED

    def AllowID(self):
        self.moderatorID.component("entry")["state"] = NORMAL

    def Body(self, master):
        self.title("Manage Moderator")
        self.moderatorID = Pmw.EntryField(master, labelpos=W,
                        label_text = "Moderator ID :")
        self.fromAddress = Pmw.EntryField(master, labelpos=W,
                        label_text = "E-Mail From Address :")
        self.name = Pmw.EntryField(master, labelpos=W,
                        label_text = "Full Name :")
        self.vacation = w = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "On Vacation :")
        w.add("No")
        w.add("Yes")
        self.userType = w = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "User Type :")
        w.add("Moderator")
        w.add("Superuser")
        w.add("Guest")
        self.createTime = Pmw.EntryField(master, labelpos=W,
                        label_text = "Create Time :", entry_state = DISABLED)
        self.newsGroupIDs = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Moderates :", orient = VERTICAL,
                        selectmode = MULTIPLE)
        self.lastLogin = Pmw.EntryField(master, labelpos=W,
                        label_text = "Last Login At :", entry_state = DISABLED)
        self.lastLogout = Pmw.EntryField(master, labelpos=W,
                        label_text = "Last Logout At :", entry_state = DISABLED)

        widgets = (self.moderatorID, self.fromAddress, self.name,
                    self.vacation, self.userType, self.createTime,
                    self.newsGroupIDs, self.lastLogin, self.lastLogout)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.moderatorID.component("entry")

    def Apply(self):
        rw = self.moderator.rw
        ro = self.moderator.ro
        ro.moderatorID = sstrip(self.moderatorID.get())
        rw.fromAddress = sstrip(self.fromAddress.get())
        rw.name = sstrip(self.name.get())
        rw.vacation = self.vacation.index(self.vacation.getcurselection())
        ro.userType = self.userType.getcurselection()
        ro.newsGroupIDs = self.newsGroupIDs.getcurselection()

