#
# Rejection management and rejection selection dialogue widget classes and
# support functions.
#

import time
import Pmw
import tkinter.messagebox
import tkinter.simpledialog
import altDialog
import cliVar
import clientEMail
from tkinter import *
from clientInterfaces import *

def UpdateRejectionDisplayList():
    app = cliVar.app
    if cliVar.currentNewsGroupID:
        cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
    if cliVar.currentNewsGroup:
        rejectionIDs = list(cliVar.currentNewsGroup.ro.rejections.keys())
    else:
        rejectionIDs = [ ]
    rejectionIDs.sort()
    app.selectRejection.component("scrolledlist").setlist(rejectionIDs)
    for button in app.rejectButtons:
        button.destroy()
    app.rejectButtons = [ ]
    for rejectionID in rejectionIDs:
        button = Button(app.cframe, text = "Reject: " + rejectionID,
                    command =
                        lambda id = rejectionID: RejectSelectedMessage(id))
        button.pack(side = LEFT, padx = 2, pady = 2)
        app.rejectButtons.append(button)

def RejectSelectedMessage(rejectionID):
    app = cliVar.app
    msg = app.messageView.GetMessage()
    newsGroup = cliVar.currentNewsGroup
    if msg and newsGroup:
        msgID = msg.ro.messageID
        if msg.ro.status in ["Rejected", "Approved"]:
            return Oops("Message '%d' already processed." % msgID)
        rejectRW = newsGroup.ro.rejections[rejectionID].rw
        action = rejectRW.defaultAction
        if action in ["Limbo & Reply", "Reject & Reply"]:
            details = clientEMail.SendEMailReply(msg, rejectRW.emailTemplate)
        else:
            details = ""
        if details != None:
            MessageReject(msg.ro.messageID, rejectionID, details)
            cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
            app.messageLists.UpdateView()

def ManageRejections():
    UpdateRejectionDisplayList()
    app = cliVar.app
    selectRejection = app.selectRejection
    selectRejection.configure(title = "%s Rejections" %
            cliVar.currentNewsGroupID)
    selectRejection.show()

def HandleManagedRejection(buttonKey):
    app = cliVar.app
    if buttonKey == None or buttonKey == "Cancel":
        app.selectRejection.withdraw()
        return
    if buttonKey == "Create":
        CreateARejection()
    sels = app.selectRejection.getcurselection()
    if len(sels) != 0:
        if buttonKey == "Edit":
            EditARejection(sels[0])
        elif buttonKey == "Delete":
            DeleteARejection(sels[0])

def CreateARejection():
    app = cliVar.app
    rejection = RejectionData("", "", RejectionRWData())
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    app.editRejectionDialog.AllowID()
    app.editRejectionDialog.SetFields(rejection)
    buttonSelect = app.editRejectionDialog.GetInput()
    if buttonSelect == "OK":
        rsp = RejectionCreate(rejection.ro.rejectionID, rejection.rw)
        if rsp == None:
            cliVar.svr = ServerGet()
            UpdateRejectionDisplayList()
            app.ShowModeratorStatus()

def EditARejection(rejectionID):
    app = cliVar.app
    if cliVar.currentNewsGroup:
        rejection = cliVar.currentNewsGroup.ro.rejections.get(rejectionID)
    if rejection == None:
        Oops("Invalid selection!")
        return
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    app.editRejectionDialog.DisallowID()
    app.editRejectionDialog.SetFields(rejection)
    buttonSelect = app.editRejectionDialog.GetInput()
    if buttonSelect == "OK":
        rsp = RejectionUpdate(rejectionID, rejection.rw)
        if rsp == None:
            cliVar.svr = ServerGet()
            UpdateRejectionDisplayList()
            app.ShowModeratorStatus()

def DeleteARejection(rejectionID):
    app = cliVar.app
    button = tkinter.messagebox.askquestion("Delete Rejection %s" % rejectionID,
                "WARNING!\n"
                "You are about to delete rejection %s.\n"
                "Are you sure you want to do that?" % rejectionID)
    if button != "yes":
        tkinter.messagebox.showinfo("Delete Aborted", "Deletion of %s aborted." %
                                rejectionID)
        return
    else:
        RejectionDelete(rejectionID)
        cliVar.svr = ServerGet()
        UpdateRejectionDisplayList()
        app.ShowModeratorStatus()

class EditRejectionDialog(altDialog.AltDialog):
    def SetFields(self, rejection):
        if self.inUse:
            return
        self.rejection = rejection
        rw = rejection.rw
        ro = rejection.ro
        self.rejectionID.setentry(ro.rejectionID)
        self.emailTemplate.settext(rw.emailTemplate)
        self.defaultAction.invoke(rw.defaultAction)
        self.createTime.setentry(LocalTimeRg(ro.createTime))
        self.creatorModeratorID.setentry(ro.creatorModeratorID)
        self.unbind("<Return>")

    def DisallowID(self):
        self.rejectionID.component("entry")["state"] = DISABLED

    def AllowID(self):
        self.rejectionID.component("entry")["state"] = NORMAL

    def Body(self, master):
        self.title("Manage Rejection")
        self.rejectionID = Pmw.EntryField(master, labelpos=W,
                        label_text = "Rejection ID :")
        self.emailTemplate = Pmw.ScrolledText(master, labelpos=N,
                        label_text = "E-Mail Response Template",
                        text_wrap = WORD)
        self.defaultAction = w = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Default Action :")
        w.add("Limbo & Reply")
        w.add("Reject & Reply")
        w.add("Reject")
        self.createTime = Pmw.EntryField(master, labelpos=W,
                        label_text = "Create Time :", entry_state = DISABLED)
        self.creatorModeratorID = Pmw.EntryField(master, labelpos=W,
                        label_text = "Created By :", entry_state = DISABLED)

        widgets = (self.rejectionID, self.emailTemplate, self.defaultAction,
                    self.createTime, self.creatorModeratorID)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.rejectionID.component("entry")

    def Apply(self):
        rw = self.rejection.rw
        ro = self.rejection.ro
        ro.rejectionID = self.rejectionID.get().strip()
        rw.emailTemplate = self.emailTemplate.get()
        rw.defaultAction = self.defaultAction.getcurselection()

