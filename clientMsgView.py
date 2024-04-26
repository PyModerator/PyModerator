#
# Right-hand main screen message view dialogue class widgets and support
# functions.
#

import Pmw
import cliVar
import sys
from tkinter import *
from clientInterfaces import *

rcvdHdr = "%sMessage %d Received As:"

class RcvdMsg(Pmw.ScrolledText):
    def __init__(self, parent):
        Pmw.ScrolledText.__init__(self, parent, labelpos=N,
                label_text = rcvdHdr % ("", 0), text_state = DISABLED,
                text_height = 10, text_wrap = WORD)

    def DisplayMessage(self, message, hdrNotes):
        self.configure(label_text = rcvdHdr % (hdrNotes, message.ro.messageID))
        if hdrNotes:
            self.configure(label_fg = "red")
        else:
            self.configure(label_fg = "black")
        hdrItems = list(message.rw.inHeaders.items())
        hdrItems.sort()
        reHdrs = ""
        otHdrs = ""
        for hdr in hdrItems:
            if hdr[0][0][:2] == "Re":
                reHdrs = "%s%s: %s\n" % (reHdrs, hdr[0][0], hdr[1])
            else:
                otHdrs = "%s%s: %s\n" % (otHdrs, hdr[0][0], hdr[1])
        msg = "%s%s\n%s" % (reHdrs, otHdrs, message.rw.inTxt)
        self.settext(msg)
        self.update_idletasks()

outHdrs = ["Subject", "From", "Reply-to", "Organization", "References",
            "Newsgroups", "Followup-to"]

class PostMsg(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.aHeader = Label(self, text = "Approved As:")
        self.aHeader.pack(side = TOP, fill = X, expand = 1)
        self.widgets = { }
        widgetOrder = [ ]
        for hdr in outHdrs:
            w = Pmw.EntryField(self, labelpos=W, label_text = hdr + " :")
            w.pack(side = TOP, fill = X, expand = 1)
            self.widgets[hdr] = w
            widgetOrder.append(w)
        Pmw.alignlabels(widgetOrder)
        self.outTxtArea = Pmw.ScrolledText(parent, text_height = 14,
                                vscrollmode = "static", hscrollmode = "none",
                                text_wrap = WORD)

    def UpdateFromIn(self, message):
        for hdr in outHdrs:
            val = message.rw.inHeaders.get((hdr, 0))
            if val != None:
                self.widgets[hdr].setentry(val)
            else:
                self.widgets[hdr].setentry("")
        if not self.widgets["Newsgroups"].get():
            self.widgets["Newsgroups"].setentry(cliVar.currentNewsGroupID)
        self.outTxtArea.settext(message.rw.inTxt)
        self.outTxtArea.configure(text_state = NORMAL)
        self.aHeader.configure(text = "Will Be Approved As:")

    def UpdateFromOut(self, message):
        for hdr in outHdrs:
            val = message.ro.outHeaders.get((hdr, 0))
            if val != None:
                self.widgets[hdr].setentry(val)
            else:
                self.widgets[hdr].setentry("")
        self.outTxtArea.settext(message.ro.outTxt)
        self.outTxtArea.configure(text_state = DISABLED)
        if message.ro.status == "Approved":
            self.aHeader.configure(text = "Was Approved As:")
        else:
            self.aHeader.configure(text = "Was Rejected")

class EvtHistory(Pmw.ScrolledListBox):
    def __init__(self, parent, evtDetail):
        Pmw.ScrolledListBox.__init__(self, parent,
                selectioncommand = self.ItemSelected,
                dblclickcommand = self.ItemSelected,
                labelpos = N, label_text = "Event History",
                listbox_width = 26
                )
        self.evtDetail = evtDetail

    def UpdateView(self, events):
        msgStrs = [ ]
        self.events = events
        for evt in events:
            msgStrs.append("%s %-7s %s" % (LocalTimeSm(evt.ro.timeStamp),
                    evt.ro.moderatorID[:7], evt.rw.eventType))
        self.setlist(msgStrs)
        self.update_idletasks()

    def ItemSelected(self, event = None):
        idxs = self.curselection()
        if len(idxs):
            evt = self.events[int(idxs[0])]
            self.evtDetail.DisplayDetail(evt)

class EvtDetail(Pmw.ScrolledText):
    def __init__(self, parent):
        Pmw.ScrolledText.__init__(self, parent, labelpos=N,
                label_text = "Event Detail", text_state = DISABLED,
                text_width = 26, text_wrap = WORD)

    def DisplayDetail(self, evt):
        self.settext(str(evt.rw.eventDetail))

msg1 = "New Material: %3d%%"
msg2 = "Bad Crossposts: %s"

class MessageView(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.message = None
        self.msgFrame = Frame(self)
        self.msgFrame.pack(side = LEFT, fill = Y, expand = 1)
        self.evtFrame = Frame(self)
        self.evtFrame.pack(side = LEFT, fill = BOTH, expand = 1)

        # Define left side: the msgFrame.
        self.rcvdMsg = RcvdMsg(self.msgFrame)
        self.rcvdMsg.pack(side = TOP, fill = Y, expand = 1)
        self.rcvdMsg.configure(vscrollmode = "static", hscrollmode = "none")
        self.analysisFrm = Frame(self.msgFrame)
        self.analysisFrm.pack(side = TOP, fill = X, expand = 1)
        fnt = self.rcvdMsg.component("text").cget("font")
        self.analysis1 = Label(self.analysisFrm, text = msg1 % 100,
                                relief = GROOVE, bd = 3, font = fnt)
        self.analysis1.pack(side = LEFT, fill = X, expand = 0)
        self.analysis2 = Pmw.ScrolledField(self.analysisFrm, text = msg2 % "")
        self.analysis2.component("entry").configure(relief = GROOVE, bd = 3,
                                width = 61, font = fnt)
        self.analysis2.pack(side = LEFT, fill = X, expand = 1)
        self.postMsg = PostMsg(self.msgFrame)
        self.postMsg.pack(side = TOP, fill = X, expand = 1)
        self.postMsg.outTxtArea.pack(side = TOP, fill = Y, expand = 1)

        # Define right side: the evtFrame.
        self.evtDetail = EvtDetail(self.evtFrame)
        self.evtHistory = EvtHistory(self.evtFrame, self.evtDetail)
        self.evtHistory.pack(side = TOP, fill = BOTH, expand = 1)
        self.evtHistory.configure(vscrollmode = "static",
                                    hscrollmode = "dynamic")
        self.evtDetail.pack(side = TOP, fill = BOTH, expand = 1)
        self.evtDetail.configure(vscrollmode = "static",
                                    hscrollmode = "dynamic")

    def GetMessage(self):
        if not self.message:
            return None
        self.postMsg.widgets
        self.message.ro.outTxt = self.postMsg.outTxtArea.get()
        if self.message.ro.status in ["Review", "Limbo"]:
            outHeaders = { }
            for hdr in outHdrs:
                val = self.postMsg.widgets[hdr].get()
                if val:
                    outHeaders[(hdr, 0)] = val
            self.message.ro.outHeaders = outHeaders
        return self.message

    def DisplayMessage(self, message, hdrNotes):
        # Update subviews.
        if not message:
            message = MessageData(-1, [], "", None, MessageRWData())
        self.message = message
        self.rcvdMsg.DisplayMessage(message, hdrNotes)
        if message.ro.status not in ["Review", "Limbo"]:
            self.postMsg.UpdateFromOut(message)
        else:
            self.postMsg.UpdateFromIn(message)
        if cliVar.currentNewsGroup:
            quotingYellow = cliVar.currentNewsGroup.rw.quotingYellow
            quotingRed = cliVar.currentNewsGroup.rw.quotingRed
        else:
            quotingYellow = 25
            quotingRed = 10
        newStuff = message.ro.newMaterial
        if newStuff > quotingYellow:
            bg1 = "grey"
        elif newStuff > quotingRed:
            bg1 = "#ff9"    # Light yellow.
        else:
            bg1 = "#f99"    # Light red.
        self.analysis1.configure(text = msg1 % newStuff, bg = bg1)
        xpost = message.ro.badCrossPosts
        if xpost:
            bg2 = "#f99"    # Light red.
        else:
            bg2 = "white"
        self.analysis2.configure(text = msg2 % message.ro.badCrossPosts)
        self.analysis2.component("entry").configure(bg = bg2)
        events = message.ro.events
        self.evtHistory.UpdateView(events)
        if events:
            self.evtDetail.DisplayDetail(events[0])
        else:
            self.evtDetail.DisplayDetail(EventData("", EventRWData()))

