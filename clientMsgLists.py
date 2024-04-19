#
# Left-hand main screen review, limbo, and srchive message list dialogue
# widget classes and support functions.
#

import Pmw
import cliVar
from types import *
from tkinter import *
from clientInterfaces import *
#import clientSearchArchive

ChunkSize = 30

class MessageLists(Frame):
    def __init__(self, parent, msgView):
        Frame.__init__(self, parent)
        self.msgView = msgView
        self.reviewList = ReviewList(self, msgView)
        self.reviewList.pack(side = TOP, fill = BOTH, expand = 1)
        self.reviewList.configure(vscrollmode = "static", hscrollmode = "none")
        self.limboList = LimboList(self, msgView)
        self.limboList.pack(side = TOP, fill = BOTH, expand = 1)
        self.limboList.configure(vscrollmode = "static", hscrollmode = "none")
        self.archiveList = ArchiveList(self, msgView)
        self.archiveList.pack(side = TOP, fill = BOTH, expand = 1)
        self.archiveList.configure(vscrollmode = "static",
                                    hscrollmode = "static")
        #w = Button(self, text = "Search Archive",
        #       command = clientSearchArchive.DoSearch)
        #w.pack(side = LEFT, expand = 1)

    def UpdateView(self):
        if cliVar.currentNewsGroupID:
            cliVar.currentNewsGroup = NewsGroupGet(cliVar.currentNewsGroupID)
        if cliVar.currentNewsGroup:
            MessageUnLock(None)
        self.reviewList.UpdateView()
        self.limboList.UpdateView()
        self.archiveList.UpdateView()
        if self.reviewList.size():
            self.reviewList.selection_set(0)
            self.reviewList.ItemSelected()
        elif self.limboList.size():
            self.limboList.selection_set(0)
            self.limboList.ItemSelected()
        else:
            self.msgView.DisplayMessage(None, "")

class GenericListing(Pmw.ScrolledListBox):
    def __init__(self, parent, msgView, listName):
        Pmw.ScrolledListBox.__init__(self, parent,
                selectioncommand = self.ItemSelected,
                dblclickcommand = self.ItemSelected,
                labelpos = N, label_text = listName,
                listbox_width = 25, listbox_height = 6
                )
        self.msgView = msgView
        self.listName = listName
        self.msgSummaries = [ ]
        self.update_idletasks()

    def UpdateView(self):
        # Repopulate msgs and msgsStr from server.
        if cliVar.currentNewsGroup == None:
            msgSummaries = [ ]
        else:
            if self.listName == "Review":
                msgIDs = cliVar.currentNewsGroup.ro.review
            else:
                msgIDs = cliVar.currentNewsGroup.ro.limbo
            msgSummaries = MessageSummaries(msgIDs)
            msgSummaries.sort()
        # Place messages assigned to us at the beginning.
        a = b = None
        us = cliVar.thisModeratorID
        for idx in range(len(msgSummaries)):
            if msgSummaries[idx][0] == us:
                b = idx
                if a == None:
                    a = idx
        if a != None:
            subset = msgSummaries[a:b+1]
            msgSummaries[a:b+1] = []
            msgSummaries[0:0] = subset
        # Now set up selection list.
        self.msgSummaries = msgSummaries
        msgStrs = [ ]
        for modID, msgID, status, subject, rcvd, fromAddr in msgSummaries:
            msgStrs.append("%-7s%5d %-12s" % (modID[:7], msgID, subject[:12]))
        self.setlist(msgStrs)
        self.update_idletasks()

    def ItemSelected(self, event = None):
        idxs = self.curselection()
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
            self.msgView.DisplayMessage(msg, hdrNotes)
        else:
            self.msgView.DisplayMessage(None, "")

class ReviewList(GenericListing):
    def __init__(self, parent, msgView):
        GenericListing.__init__(self, parent, msgView, "Review")

class LimboList(GenericListing):
    def __init__(self, parent, msgView):
        GenericListing.__init__(self, parent, msgView, "Limbo")

class ArchiveList(GenericListing):
    def __init__(self, parent, msgView):
        GenericListing.__init__(self, parent, msgView, "Archive")
        self.currentNewsGroup = None
        self.msgSummaries = [ ]

    def UpdateChunkAt(self, toID):
        # Read 50 messages from server at toID and refresh display.
        if cliVar.currentNewsGroup:
            fromID = max(toID - ChunkSize, 0)
            self.msgSummaries[fromID:toID] = \
                        MessageSummaries(list(range(fromID, toID)))
        msgStrs = [ ]
        for modID, msgID, status, subject, rcvd, fromAddr in self.msgSummaries:
            msgStrs.append("%s%5d %-8s [%-25s] %-25s" % (LocalTimeSm(rcvd),
                    msgID, status[:8], CleanCut(fromAddr, 25),
                    CleanCut(subject, 25)))
        msgStrs.reverse()
        self.setlist(msgStrs)
        self.update_idletasks()

    def UpdateView(self):
        # Read 50 top messages from server and display them.
        if self.currentNewsGroup != cliVar.currentNewsGroup:
            self.currentNewsGroup = cliVar.currentNewsGroup
            self.msgSummaries = [ ]
        if cliVar.currentNewsGroup:
            lastID = cliVar.currentNewsGroup.ro.numMessages
            sumLen = len(self.msgSummaries)
            newRows = [ ]
            for idx in range(sumLen, lastID):
                newRows.append(EmptySummary(idx, "-"))
            self.msgSummaries = self.msgSummaries + newRows
        else:
            lastID = 0
            self.msgSummaries = [ ]
        self.UpdateChunkAt(lastID)

    def ItemSelected(self, event = None):
        idxs = self.curselection()
        if len(idxs):
            idx = int(idxs[0])
            messageID = len(self.msgSummaries) - idx - 1
            msgSummary = self.msgSummaries[messageID]
            if msgSummary[2] == "-":
                self.UpdateChunkAt(messageID + 1)
                self.see(idx)
            MessageUnLock(None)
            lockStatus = MessageLock(messageID)
            if lockStatus not in [1, None]:
                hdrNotes = lockStatus
            else:
                hdrNotes = ""
            msg = MessageGet(messageID)
            self.msgView.DisplayMessage(msg, hdrNotes)
        else:
            self.msgView.DisplayMessage(None, "")

