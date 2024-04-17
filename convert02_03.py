#!/usr/bin/env python

import cPickle
from convTime import StrTimeToInt
from  commonDefs02 import *
import serVar

# Read old server data.

dataFile = open(serVar.path + "/server.cfg", "rb+")
dataFile.seek(0)
appVersion = cPickle.load(dataFile)
ro, rw, cryptedPasswords = cPickle.load(dataFile)

# Do conversions.

rw.idleTimeLogout = 900

for moderator in ro.moderators.values():
    print moderator.ro.moderatorID
    if moderator.ro.superuser:
        moderator.ro.userType = "Superuser"
    else:
        moderator.ro.userType = "Moderator"
    moderator.ro.createTime = StrTimeToInt(moderator.ro.createTime)
    moderator.ro.lastLogin = StrTimeToInt(moderator.ro.lastLogin)
    moderator.ro.lastLogout = StrTimeToInt(moderator.ro.lastLogout)
    moderator.rw.vacation = 0
    del moderator.ro.superuser
    del moderator.rw.moderatorAlias
    del moderator.rw.alertAddress

# Write new server data out.

dataFile.seek(0)
cPickle.dump("0.3", dataFile, 1)
cPickle.dump((ro, rw, cryptedPasswords), dataFile, 1)
dataFile.close()

for newsGroupID in ro.newsGroupIDs:
    print newsGroupID
    # Read old newsgroup data.
    baseDir = "%s/%s" % (serVar.path, newsGroupID)
    baseCfg = "%s/%s" % (baseDir, "newsGroupData.cfg")
    grpFile = open(baseCfg, "rb+")
    grpFile.seek(0)
    newsGroup = cPickle.load(grpFile)

    # Do conversion
    newsGroup.ro.createTime = StrTimeToInt(newsGroup.ro.createTime)
    newsGroup.ro.statistics = stats = {"": ["Approved", "Limboed"]}
    newsGroup.rw.periodicPosts = { }
    newsGroup.rw.quotingYellow = 25
    newsGroup.rw.quotingRed = 10
    del newsGroup.rw.idleTimeLogout

    for rejection in newsGroup.ro.rejections.values():
        rejection.ro.createTime = StrTimeToInt(rejection.ro.createTime)

    # Convert messages:
    for messageID in range(newsGroup.ro.numMessages):
        print messageID
        # Read old message data.
        msg = cPickle.load(open("%s/%06d" % (baseDir, messageID), "rb+"))

        # Do conversion.
        for event in msg.ro.events:
            event.ro.timeStamp = StrTimeToInt(event.ro.timeStamp)
            moderatorID = event.ro.moderatorID
            modRow = stats.get(moderatorID)
            if not modRow:
                modRow = stats[moderatorID] = len(stats[""])*[ 0 ]
            if event.rw.eventType == "Approved":
                col = 0
            elif event.rw.eventType == "Limbo":
                col = 1
            elif event.rw.eventType[:7] == "Reject:":
                rejectID = event.rw.eventType[8:]
                if rejectID not in stats[""]:
                    for k, v in stats.items():
                        if k == "":
                            v.append(rejectID)
                        else:
                            v.append(0)
                col = stats[""].index(rejectID)
            else:
                evt = event.rw.eventType
                col = -1
                if evt not in ["", "Received", "Assigned", "Email", "Reassign",
                                "Note"]:
                    if evt not in stats[""]:
                        for k, v in stats.items():
                            if k == "":
                                v.append(evt)
                            else:
                                v.append(0)
                    col = stats[""].index(evt)
            if col >= 0:
                modRow[col] = modRow[col] + 1

        # Write new message data.
        cPickle.dump(msg, open("%s/%06d" % (baseDir, messageID), "wb+"), 1)

    # Write new newsgroup data.
    grpFile.seek(0)
    cPickle.dump(newsGroup, grpFile, 1)
    grpFile.close()

