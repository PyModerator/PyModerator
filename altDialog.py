#
# Adapted from tkSimpleDialog.py. A simple dialog widget base class.
#

from tkinter import *

class AltDialog(Toplevel):
    def __init__(self, parent, title = None,
                    okName = "OK", cancelName = "Cancel"):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        self.inUse = 0
        self.go_var = StringVar()
        self.withdraw()
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = Frame(self)
        self.initial_focus = self.Body(body)
        body.pack(padx=5, pady=5)
        self.ButtonBox(okName, cancelName)

        self.protocol("WM_DELETE_WINDOW", self.Cancel)
        self.geometry("+%d+%d" % (self.parent.winfo_rootx() + 50,
                                  self.parent.winfo_rooty() + 50))

    def GetInput(self):
        if self.inUse:
            return
        self.inUse = 1
        self.deiconify()
        #self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.initial_focus.focus_set()
        self.wait_variable(self.go_var)
        self.withdraw()
        self.parent.focus_set()
        self.inUse = 0
        self.update_idletasks()
        return self.go_var.get()

    def Body(self, master):
        # Override to create the body of the dialog. Return widget that
        # should have the initial focus.
        pass

    def ButtonBox(self, okName, cancelName):
        # Add standard button box. Override if you don't want the
        # standard buttons.
        box = Frame(self)
        w = Button(box, text=okName, width=10, command=self.Ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text=cancelName, width=10, command=self.Cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind("<Return>", self.Ok)
        self.bind("<Escape>", self.Cancel)
        box.pack()

    def Ok(self, event = None):
        if not self.Validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.Apply()
        self.go_var.set("OK")

    def Cancel(self, event = None):
        self.go_var.set("Cancel")

    def Delete(self, event = None):
        self.parent.focus_set()
        self.withdraw()
        self.destroy()

    def Validate(self):
        # Override to validate input. Return false if validation fails.
        return 1

    def Apply(self):
        # Override. This does any processing after "Ok" and validation
        # has passed.
        pass

