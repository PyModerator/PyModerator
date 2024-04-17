#
# E-mail dialogue widgets and support functions.
#

import Pmw
import altDialog
import cliVar
import string
import smtplib
import sys
from Tkinter import *
from clientInterfaces import *

sstrip = string.strip

def SendEMailReply(message, otherText):
    app = cliVar.app
    if cliVar.sockFile == None:
        Oops("Not logged in!")
        return None
    rw = cliVar.thisModerator.rw
    fromAddr = '"%s" <%s>' % (rw.name, rw.fromAddress)
    if message:
        toLine = message.rw.inHeaders.get(("Reply-to", 0))
        if not toLine:
            toLine = message.rw.inHeaders.get(("From", 0))
            if not toLine:
                toLine = ""
        subjectLine = message.rw.inHeaders.get(("Subject", 0))
        if subjectLine:
            if string.lower(subjectLine[:3]) <> "re:":
                subjectLine = "Re: " + subjectLine
        else:
            subjectLine = ""
        newsGroupsLine = message.rw.inHeaders.get(("Newsgroups", 0))
        if not newsGroupsLine:
            newsGroupsLine = ""
        bodyLines = "\n%s\n---Original Message---\n" \
                    "Subject: %s\nNewsgroups: %s\n%s" % (otherText,
                            subjectLine, newsGroupsLine, message.rw.inTxt)
    else:
        toLine = subjectLine = ""
        bodyLines = otherText
    dialog = app.emailDialog
    dialog.SetFields(fromAddr, toLine, subjectLine, bodyLines)
    buttonSelect = dialog.GetInput()
    if buttonSelect <> "OK":
        return None
    allAddrs = filter(None, map(string.strip,
                string.split(dialog.toLine + "," + dialog.bccLine, ",")))
    msgBody = string.join(WordWrap(string.split(dialog.bodyLines, "\n")), "\n")
    outHeaders = { ("From", 0): dialog.fromLine, ("To", 0): dialog.toLine,
                    ("Subject", 0): dialog.subjectLine }
    msg, errMsg = EmailMessage(allAddrs, outHeaders, msgBody,
                                app.cache.smtpHost)
    if errMsg:
        Oops(errMsg)
    return msg

class EMailDialog(altDialog.AltDialog):
    def SetFields(self, fromLine, toLine, subjectLine, bodyLines):
        if self.inUse:
            return
        self.fromLine = fromLine
        self.toLine = toLine
        self.bccLine = ""
        self.subjectLine = subjectLine
        self.bodyLines = bodyLines
        self.fromLineW.setentry(fromLine)
        self.toLineW.setentry(toLine)
        self.bccW.setentry(self.bccLine)
        self.subjectLineW.setentry(subjectLine)
        self.bodyLinesW.settext(bodyLines)
        self.unbind("<Return>")

    def Body(self, master):
        self.title("E-Mail Reply")
        self.fromLineW = Pmw.EntryField(master, labelpos=W,
                        label_text = "From :")
        self.toLineW = Pmw.EntryField(master, labelpos=W,
                        label_text = "To :")
        self.bccW = Pmw.EntryField(master, labelpos=W,
                        label_text = "Bcc :")
        self.subjectLineW = Pmw.EntryField(master, labelpos=W,
                        label_text = "Subject :")
        self.bodyLinesW = Pmw.ScrolledText(master, vscrollmode = 'static',
                                            text_wrap = WORD)

        widgets = (self.fromLineW, self.toLineW, self.bccW,
                    self.subjectLineW, self.bodyLinesW)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.bodyLinesW.component("text")

    def Apply(self):
        self.fromLine = sstrip(self.fromLineW.get())
        self.toLine = sstrip(self.toLineW.get())
        self.bccLine = sstrip(self.bccW.get())
        self.subjectLine = sstrip(self.subjectLineW.get())
        self.bodyLines = self.bodyLinesW.get()

