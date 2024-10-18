PyModerator
===========

PyModerator is used to moderate Usenet newsgroups. It is written in Python, a
high level scripting language. Python has been ported to many different
operating systems, so PyModerator can run on any system that can run Python
and the Python GUI module Tkinter. This includes most Unix systems, most
Microsoft Windows systems, and the Apple Macintosh. It has not been tested on
any Macintosh system though.

A single moderator (solo moderation) or a group of cooperating moderators
(co-moderation) may use PyModerator to moderate one or more newsgroups. While
it can be used very effectively to solo moderate, many of its features were
specifically designed to aid co-moderation.

PyModerator is really composed of two processing pieces: a client Graphical
User Interface (GUI) process and a server (central repository) process. The
two processes communicate via a TCP/IP socket, which allows them to run on
different machines. The server process listens on a TCP/IP service port for
client connections. A single server can handle any number of clients and
therefore any number of concurrently active moderators. If you have several
co-moderators and one of them can leave their machine on (and accessible to
the net), then that moderator can run the server process continuously and all
the co-moderators can connect to that central server using only the client
program. PyModerator features are best utilized if one person hosts a server
(runs serverStart.py) and each of the co-moderators run a client (runs
clientStart.py). Otherwise each co-moderator can run in solo-moderation mode
by running startBoth.py which starts a local server and a local client. But if
each co-moderator runs a local server, it will unfortunately segment the
archives across all their machines.

Requirements
------------

To run PyModerator on your computer you will need to install the Python
interpreter (if you do not already have it installed). PyModerator works with
Python 3, up to and including Python 3.11. Later versions are not yet
supported, due to some necessary modules being removed from the Python
standard library, but support for the latest versions will be added very soon.

Installation
------------

To install PyModerator, first download the latest release from:

https://github.com/PyModerator/PyModerator/releases

Then unzip the file into a folder or directory of your choosing. Ensure that
the drive or file system has enough room to hold archived messages (which may
accumulate to many megabytes after a few years). In general you should install
to a user account that has the minimum authorizations needed to run (it is
recommended that you not run either the client or server as root on Unix
systems).

On Microsoft Windows, PyModerator does not use an Install Shield and therefore
no entry is made in the registry. You uninstall simply by deleting the
PyModerator folder.

Using PyModerator
-----------------

A full guide to configuring and using PyModerator is available from:

https://lugoj.com/products.html

