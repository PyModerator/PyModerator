#
# Dialogue widgets and support functions for archive searches.
#

import Pmw
import altDialog
import cliVar
import string
from Tkinter import *
from clientInterfaces import *

def DoSearch():
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return
    app = cliVar.app
    app.searchDialog.GetInput()

class SearchDialog(altDialog.AltDialog):
    def __init__(self, parent):
        altDialog.AltDialog.__init__(self, parent, title = "Archive Search",
                                    okName = "Search", cancelName = "Close")
        self.msgSummaries = []
        self.searchExpW.setentry("")
        self.slistW.setlist([])
        self.ignoreCaseW.invoke(1)
        self.itemNamesW.invoke(0)
        self.itemNamesW.invoke(1)

    def Body(self, master):
        self.title("Search Archive")
        self.searchExpW = Pmw.EntryField(master, labelpos=W,
                        label_text = "Search Expression :")
        self.ignoreCaseW = w = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Ignore Case :")
        w.add("No")
        w.add("Yes")
        self.itemNamesW = Pmw.RadioSelect(master, labelpos=W,
                        label_text = "Search In :", orient = HORIZONTAL,
                        selectmode = MULTIPLE)
        for itemName in ["Incoming Headers", "Incoming Bodies",
                            "Outgoing Headers", "Outgoing Bodies",
                            "History Events"]:
            self.itemNamesW.add(itemName)

        self.slistW = Pmw.ScrolledListBox(master,
                        selectioncommand = self.ItemSelected,
                        dblclickcommand = self.ItemSelected,
                        labelpos = N, label_text = "Results",
                        vscrollmode = "static", listbox_width = 80)
        widgets = (self.searchExpW, self.ignoreCaseW,
                    self.itemNamesW, self.slistW)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.searchExpW.component("entry")

    def ItemSelected(self, event = None):
        idxs = self.slistW.curselection()
        if len(idxs):
            msgSummary = self.msgSummaries[int(idxs[0])]
            messageID = msgSummary[1]
            MessageUnLock(None)
            lockStatus = MessageLock(messageID)
            if lockStatus not in [1, None]:
                hdrNotes = lockStatus
            else:
                hdrNotes = ""
            msg = MessageGet(messageID)
            cliVar.app.messageView.DisplayMessage(msg, hdrNotes)

    def Validate(self):
        searchExp = string.strip(self.searchExpW.get())
        ignoreCase = self.ignoreCaseW.index(self.ignoreCaseW.getcurselection())
        itemNames = self.itemNamesW.getcurselection()
        if cliVar.currentNewsGroup == None:
            msgSummaries = [ ]
        else:
            msgSummaries = SearchArchive(searchExp, ignoreCase, itemNames)
            msgSummaries.reverse()
        self.msgSummaries = msgSummaries
        msgStrs = [ ]
        for modID, msgID, status, subject, rcvd, fromAddr in msgSummaries:
            msgStrs.append("%s%6d %-8s [%-25s] %-25s" % (LocalTimeSm(rcvd),
                    msgID, status[:8], CleanCut(fromAddr, 25),
                    CleanCut(subject, 25)))
        self.slistW.setlist(msgStrs)
        self.update_idletasks()
        return 0

