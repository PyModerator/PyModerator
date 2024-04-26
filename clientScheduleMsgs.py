#
# Dialogue widgets and support functions for scheduling repeated messages.
#

import Pmw
import altDialog
import cliVar
from tkinter import *
from clientInterfaces import *

secsPerDay = 24.0*3600.0

def PeriodicPosts():
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    if not cliVar.currentNewsGroup:
        Oops("No valid newsgroup set.")
        return
    app = cliVar.app
    app.scheduleDialog.SetFields()
    app.scheduleDialog.GetInput()

class ScheduleDialog(altDialog.AltDialog):
    def __init__(self, parent):
        altDialog.AltDialog.__init__(self, parent, title = "Archive Search")
        self.messageIDs = [ ]
        self.lastIdxs = ()

    def SetFields(self):
        if self.inUse:
            return
        self.dTime = cliVar.app.svrClockFaster
        self.UpdateDisplay()

    def UpdateDisplay(self, msgID = None):
        grp = cliVar.currentNewsGroup
        self.messageIDs = list(grp.rw.periodicPosts.keys())
        self.messageIDs.sort()
        self.slistW.setlist(list(map(str, self.messageIDs)))
        if self.messageIDs:
            if msgID != None and msgID in self.messageIDs:
                idx = self.messageIDs.index(msgID)
            else:
                idx = 0
            self.slistW.selection_set(idx)
            self.ItemSelected()

    def AddMsg(self, event = None):
        app = cliVar.app
        grp = cliVar.currentNewsGroup
        msg = app.messageView.GetMessage()
        if msg:
            if msg.ro.status != "Approved":
                return Oops("You may only repeat approved messages.")
            messageID = msg.ro.messageID
            if messageID not in grp.rw.periodicPosts:
                repeatTime = 30.0*secsPerDay
                nextSendTime = msg.ro.events[0].ro.timeStamp + repeatTime
                grp.rw.periodicPosts[messageID] = [ nextSendTime, repeatTime ]
                NewsGroupUpdate(grp.ro.newsGroupID, grp.rw)
                self.UpdateDisplay(messageID)
        self.initial_focus.focus_set()

    def DropMsg(self, event = None):
        idxs = self.lastIdxs
        if len(idxs) and len(self.messageIDs):
            grp = cliVar.currentNewsGroup
            messageID = self.messageIDs[int(idxs[0])]
            del grp.rw.periodicPosts[messageID]
            NewsGroupUpdate(grp.ro.newsGroupID, grp.rw)
            self.UpdateDisplay()
        self.initial_focus.focus_set()

    def UpdateSched(self, event = None):
        idxs = self.lastIdxs
        if len(idxs) and len(self.messageIDs) > 0:
            grp = cliVar.currentNewsGroup
            messageID = self.messageIDs[int(idxs[0])]
            repeatTimeD = float(self.repeatTimeW.get())
            nextSendTimeD = float(self.nextSendTimeW.get())
            repeatTime = repeatTimeD*secsPerDay
            nextSendTime = TimeNow() + self.dTime + nextSendTimeD*secsPerDay 
            grp.rw.periodicPosts[messageID] = [ nextSendTime, repeatTime ]
            NewsGroupUpdate(grp.ro.newsGroupID, grp.rw)
            self.UpdateDisplay(messageID)
        self.initial_focus.focus_set()

    def ButtonBox(self, okName, cancelName):
        box = Frame(self)
        w = Button(box, text = "Add", width=10, command=self.AddMsg,
                    default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text = "Drop", width=10, command=self.DropMsg)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text = "Update", width=10, command=self.UpdateSched)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Close", width=10, command=self.Cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind("<Return>", self.UpdateSched)
        self.bind("<Escape>", self.Cancel)
        box.pack()

    def Body(self, master):
        self.title("Periodic Message Postings")
        self.slistW = Pmw.ScrolledListBox(master,
                        selectioncommand = self.ItemSelected,
                        dblclickcommand = self.ItemSelected,
                        labelpos = N, label_text = "Repeated Messages",
                        vscrollmode = "static")
        self.repeatTimeW = Pmw.EntryField(master, labelpos=W,
                        label_text = "Repetition time, in days :",
                        validate = "real")
        self.nextSendTimeW = Pmw.EntryField(master, labelpos=W,
                        label_text = "Next send time, in days :",
                        validate = "real")
        widgets = (self.slistW, self.nextSendTimeW, self.repeatTimeW)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.repeatTimeW.component("entry")

    def ItemSelected(self, event = None):
        idxs = self.slistW.curselection()
        if not idxs:
            idxs = self.lastIdxs
        self.lastIdxs = idxs
        if len(idxs) and len(self.messageIDs):
            grp = cliVar.currentNewsGroup
            messageID = self.messageIDs[int(idxs[0])]
            MessageUnLock(None)
            lockStatus = MessageLock(messageID)
            if lockStatus not in [1, None]:
                hdrNotes = lockStatus
            else:
                hdrNotes = ""
            msg = MessageGet(messageID)
            cliVar.app.messageView.DisplayMessage(msg, hdrNotes)
            repeatTime = 30.0*secsPerDay
            nextSendTime = TimeNow() + self.dTime + repeatTime
            if messageID in grp.rw.periodicPosts:
                nextSendTime, repeatTime = grp.rw.periodicPosts[messageID]
            nextSendTimeD = (nextSendTime - TimeNow() - self.dTime)/secsPerDay
            repeatTimeD = repeatTime/secsPerDay
            self.repeatTimeW.setentry("%7.3f" % repeatTimeD)
            self.nextSendTimeW.setentry("%7.3f" % nextSendTimeD)

