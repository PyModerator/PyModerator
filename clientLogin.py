#
# Login dialogue widget class and support functions.
#

import Pmw
import tkinter.messagebox
import tkinter.simpledialog
import altDialog
import cliVar
from tkinter import *
from clientInterfaces import *

class EditLoginData(altDialog.AltDialog):
    def SetFields(self):
        if self.inUse:
            return
        cache = cliVar.app.cache
        self.moderatorID.setentry(cache.loginID)
        self.serviceHost.setentry(cache.serviceHost)
        self.servicePort.setentry(str(cache.servicePort))
        self.nntpHost.setentry(cache.nntpHost)
        self.nntpPort.setentry(str(cache.nntpPort))
        self.nntpSecurity.setvalue(str(cache.nntpSecurity))
        self.nntpUser.setentry(cache.nntpUser)
        self.nntpPassword.setentry(cache.nntpPassword)
        self.smtpHost.setentry(cache.smtpHost)
        self.smtpSecurity.setvalue(str(cache.smtpSecurity))

    def Body(self, master):
        self.title("Edit Default Login Fields")
        self.moderatorID = Pmw.EntryField(master, labelpos=W,
                            label_text = "Moderator ID :")
        self.serviceHost = Pmw.EntryField(master, labelpos=W,
                            label_text = "Service Host :")
        self.servicePort = Pmw.EntryField(master, labelpos=W,
                            label_text = "Service Port :", validate = "numeric")
        self.nntpHost = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP Host :")
        self.nntpPort = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP Port :", validate = "numeric")
        self.nntpSecurity = Pmw.OptionMenu(master, labelpos=W,
                            label_text = "NNTP Security :",
                            items = ["Plaintext", "STARTTLS", "SSL"])
        self.nntpUser = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP User :")
        self.nntpPassword = Pmw.EntryField(master, labelpos=W,
                            label_text = "NNTP Password :")
        self.smtpHost = Pmw.EntryField(master, labelpos=W,
                            label_text = "SMTP Host :")
        self.smtpSecurity = Pmw.OptionMenu(master, labelpos=W,
                            label_text = "SMTP Security :",
                            items = ["Plaintext", "STARTTLS", "SSL"])
        widgets = (self.moderatorID, self.serviceHost, self.servicePort,
                   self.nntpHost, self.nntpPort, self.nntpSecurity,
                   self.nntpUser, self.nntpPassword, self.smtpHost,
                   self.smtpSecurity)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.moderatorID.component("entry")

    def Apply(self):
        app = cliVar.app
        cache = app.cache
        cache.loginID = self.moderatorID.get().strip()
        cache.serviceHost = self.serviceHost.get().strip()
        cache.servicePort = int(self.servicePort.get().strip())
        cache.nntpHost = self.nntpHost.get().strip()
        cache.nntpPort = int(self.nntpPort.get().strip())
        cache.nntpSecurity = self.nntpSecurity.getvalue()
        cache.nntpUser = self.nntpUser.get().strip()
        cache.nntpPassword = self.nntpPassword.get()
        cache.smtpHost = self.smtpHost.get().strip()
        cache.smtpSecurity = self.smtpSecurity.getvalue()
        app.WriteCache()

class LoginDialog(altDialog.AltDialog):
    def SetFields(self):
        if self.inUse:
            return
        app = cliVar.app
        cache = app.cache
        self.moderatorID.setentry(cache.loginID)
        self.password.setentry(app.password)

    def Body(self, master):
        self.title("Connect and Login to Server")
        self.moderatorID = Pmw.EntryField(master, labelpos=W,
                            label_text = "Moderator ID :")
        self.password = Pmw.EntryField(master, labelpos=W,
                            label_text = "Password :")
        self.password.component("entry")["show"] = "*"
        widgets = (self.moderatorID, self.password)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.password.component("entry")

    def Apply(self):
        app = cliVar.app
        cache = app.cache
        cache.loginID = self.moderatorID.get().strip()
        app.password = self.password.get()

class ChangePassword(altDialog.AltDialog):
    def SetFields(self):
        if self.inUse:
            return
        app = cliVar.app
        cache = app.cache
        self.moderatorID.setentry(cache.loginID)
        self.password1.setentry(app.password)
        self.password2.setentry(app.password)

    def Body(self, master):
        self.title("Change Moderator's Password")
        self.moderatorID = Pmw.EntryField(master, labelpos=W,
                            label_text = "Moderator ID :")
        self.password1 = Pmw.EntryField(master, labelpos=W,
                            label_text = "Password :")
        self.password1.component("entry")["show"] = "*"
        self.password2 = Pmw.EntryField(master, labelpos=W,
                            label_text = "Password again :")
        self.password2.component("entry")["show"] = "*"
        widgets = (self.moderatorID, self.password1, self.password2)
        for w in widgets:
            w.pack(fill=X, expand=1, padx=10, pady=5)
        Pmw.alignlabels(widgets)
        return self.moderatorID.component("entry")

    def Validate(self):
        mID = self.moderatorID.get().strip()
        pw1 = self.password1.get()
        pw2 = self.password2.get()
        if pw1 != pw2:
            Oops("Password fields do not match.")
        else:
            rsp = ModeratorChangePW(mID, pw1)
            if rsp == None:
                if mID == cliVar.app.cache.loginID:
                    cliVar.app.password = pw1
                return 1
        return 0

