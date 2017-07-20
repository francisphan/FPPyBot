#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ssl
import sys
import time
import socket
import threading
import re
import yaml

# Setup the IRC connection
irc = socket.socket()
irc = ssl.wrap_socket(irc)

with open("secrets.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
# Edit these values for your server
ircServer = cfg['server'] if cfg['server'] else 'foobar'
ircSSLPort = cfg['port'] if cfg['port'] else 6667
ircNick = cfg['nick'] if cfg['nick'] else 'FPPyBot'
# What the bot uses as a command character
ircCKey = "!"
cHannel = cfg['channel'] if cfg['channel'] else 'test-channel'

# List of people not allowed to do commands until CRs are done
bl = cfg['bl']

def rawSend(data):
    irc.send(data + "\r\n")

def ircConnect():
    irc.connect((ircServer, ircSSLPort))

def ircMessage(msg, channel):
    rawSend("PRIVMSG " + channel + " :" + msg + "\r\n")

def ircRegister():
    rawSend("USER " + ircNick + " 0 * " + ":" + ircNick + "\r\n")

def ircSendNick():
    rawSend("NICK " + ircNick + "\r\n")

def ircJoin(channel):
    rawSend("JOIN " + channel + "\r\n")


def annoyForCRs(channel, nickname=False):

    # Annoy Everyone
    if not nickname:
        for person in cfg['people']:
            if len(cfg['people'][person]['crs']) != 0:
                ircMessage("Automated Annoyance from " + person, channel)
                for cr in cfg['people'][person]['crs']:
                    people = ' '.join(str(reviewer) for reviewer in cfg['people'][person]['crs'][cr])
                    ircMessage("[" + people + "] " + cr, channel)
    else:
        if len(cfg['people'][nickname]['crs']) != 0:
            ircMessage("Outstanding CRs for " + nickname, channel)
            for cr in cfg['people'][nickname]['crs']:
                people = ' '.join(str(reviewer) for reviewer in cfg['people'][nickname]['crs'][cr])
                ircMessage("[" + people + "] " + cr, channel)

def dataParser(data):
    matches = re.match('\:(.+?)!(.+?)@(.+?)\s.+?:(.+)', data)
    return matches.group(1), matches.group(2), matches.group(3), matches.group(4)

def printHelp(channel):
    ircMessage("AvailableCommands: prepend command with !", channel)
    ircMessage(" - annoyForCRs", channel)
    ircMessage(" - blacklist [people]", channel)
    ircMessage(" - whitelist [people]", channel)
    ircMessage(" - writeListsToFile", channel)
    ircMessage(" - removeCR [CRs]", channel)
    ircMessage(" - addCR [CRs]", channel)
    ircMessage(" - listCRs", channel)
    ircMessage(" - addReviewer [CR] [reviewers]", channel)
    ircMessage(" - removeReviewer [CR] [reviewers]", channel)

def Initialize():
    ircConnect()
    ircRegister()
    ircSendNick()
    ircJoin(cHannel)

def blacklist(command, channel):
    matches = re.match('.*!blacklist\s(.+?)[\r\n!].*', command)
    if matches == None:
        ircMessage("You broke me :( I don't know how to handle that", channel)
    else:
        toAdd = filter(None, matches.group(1).split(' '))
        for person in toAdd:
            if person == 'phanfran':
                ircMessage("I never ignore my creator Francis", channel)
            elif person in bl:
                ircMessage(person + " already in blacklist", channel)
            else:
                ircMessage("Adding " + person + " to blacklist", channel)
                bl.append(person)
                cfg['bl'] = bl

def whitelist(command, channel):
    matches = re.match('.*!whitelist\s(.+?)[\r\n!].*', command)
    if matches == None:
        ircMessage("You broke me :( I don't know how to handle that", channel)
    else:
        toRemove = filter(None, matches.group(1).split(' '))
        for person in toRemove:
            if person in bl:
                ircMessage("Removing " + person + " from blacklist", channel)
                bl.remove(person)
                cfg['bl'] = bl
            else:
                ircMessage(person + " not in blacklist", channel)


def writeListsToFile(channel):
    ircMessage("Saving lists to secrets", channel)
    with open('secrets.yml', 'w') as ymlfile:
        yaml.dump(cfg, ymlfile, default_flow_style=False)

def removeCR(nickname, command, channel):
    matches = re.match('.*!removeCR\s(.+?)[\r\n!].*', command)
    if matches == None:
        ircMessage("You broke me :( I don't know how to handle that", channel)
    else:
        toRemove = filter(None, matches.group(1).split(' '))
        for cr in toRemove:
            try:
                cfg['people'][nickname]['crs'][cr]
                ircMessage("Removing " + cr + " from list of CRs for " + nickname, channel)
                del cfg['people'][nickname]['crs'][cr]
            except KeyError:
                ircMessage(cr + " is not in list of CRs for " + nickname, channel)

def addCR(nickname, command, channel):
    matches = re.match('.*!addCR\s(.+?)[\r\n!].*', command)
    if matches == None:
        ircMessage("You broke me :( I don't know how to handle that", channel)
    else:
        toAdd = filter(None, matches.group(1).split(' '))
        for cr in toAdd:
            try:
                cfg['people'][nickname]['crs'][cr]
                ircMessage(cr + " already on list of CRs", channel)
            except KeyError:
                ircMessage("Adding " + cr + " to list of CRs for " + nickname, channel)
                cfg['people'][nickname]['crs'][cr] = []

def listCRs(nickname, channel):
    if len(cfg['people'][nickname]['crs']) != 0:
        ircMessage("Outstanding CRs for " + nickname, channel)
        for cr in cfg['people'][nickname]['crs']:
            ircMessage(cr, channel)
    else:
        ircMessage("No CRs found posted by " + nickname, channel)

def removeReviewer(nickname, command, channel):
    matches = re.match('.*!removeReviewer\s(.+?)\s(.+?)[\r\n!].*', command)
    if matches == None:
        ircMessage("You broke me :( I don't know how to handle that", channel)
    else:
        cr = matches.group(1)
        toRemove = filter(None, matches.group(2).split(' '))
        for reviewer in toRemove:
            try:
                if reviewer in cfg['people'][nickname]['crs'][cr]:
                    ircMessage("Removing " + reviewer + " from " + cr, channel)
                    cfg['people'][nickname]['crs'][cr].remove(reviewer)
                else:
                    ircMessage(reviewer + " is not on this CR", channel)
            except KeyError:
                ircMessage(cr + " isn't on your list of CRs", channel)

def addReviewer(nickname, command, channel):
    matches = re.match('.*!addReviewer\s(.+?)\s(.+?)[\r\n!].*', command)
    if matches == None:
        ircMessage("You broke me :( I don't know how to handle that", channel)
    else:
        cr = matches.group(1)
        toAdd = filter(None, matches.group(2).split(' '))
        for reviewer in toAdd:
            try:
                if reviewer not in cfg['people'][nickname]['crs'][cr]:
                    ircMessage("Adding " + reviewer + " to " + cr, channel)
                    cfg['people'][nickname]['crs'][cr].append(reviewer)
                else:
                    ircMessage(reviewer + " is already on this CR", channel)
            except KeyError:
                ircMessage(cr + " isn't on your list of CRs", channel)

def listReviewers(nickname, channel):
    if len(cfg['people'][nickname]['reviewers']) != 0:
        ircMessage("Reviewers for " + nickname, channel)
        for reviewer in cfg['people'][nickname]['reviewers']:
            ircMessage("- " + reviewer, channel)
    else:
        ircMessage("No Reviewers found for " + nickname, channel)

def channelRequests(channel, data):
    '''Process all of the commands into the channel'''

    nickname, user, address, command = dataParser(data)
    command = command + "\r\n"
    if (user in bl or nickname in bl) and ircCKey in command:
        ircMessage("I was told never to listen to you", channel)

    else:
        # Checks for a persons list of reviewers and crs
        # Creates it if they don't exist
        try:
            cfg['people'][nickname]
        except KeyError:
            cfg['people'][nickname] = { 'crs': {} }

        workFlag = False
        if ircCKey + "help" in command:
            printHelp(channel)
            workFlag = True

        # !ping to see if the bot is alive
        if ircCKey + "ping" in command:
            ircMessage("pong", channel)
            workFlag = True

        if ircCKey + "blacklist " in command:
            blacklist(command, channel)
            workFlag = True

        if ircCKey + "whitelist " in command:
            whitelist(command, channel)
            workFlag = True

        if ircCKey + "writeListsToFile" in command:
            writeListsToFile(channel)
            workFlag = True

        if ircCKey + "removeCR " in command:
            removeCR(nickname, command, channel)
            workFlag = True

        if ircCKey + "addCR " in command:
            addCR(nickname, command, channel)
            workFlag = True

        if ircCKey + "listCRs" in command:
            listCRs(nickname, channel)
            workFlag = True

        if ircCKey + "removeReviewer " in command:
            removeReviewer(nickname, command, channel)
            workFlag = True

        if ircCKey + "addReviewer " in command:
            addReviewer(nickname, command, channel)
            workFlag = True

        if ircCKey + "listReviewers" in command:
            listReviewers(nickname, channel)
            workFlag = True

        if ircCKey + "annoyForCRs" in command:
            annoyForCRs(channel, nickname)
            workFlag = True

        if ircCKey + "QUIT" in command and user == 'phanfran' and nickname == 'phanfran':
            ircMessage("Goodnight everyone", channel)
            writeListsToFile(channel)
            sys.exit()

        if ircCKey in command and not workFlag:
            ircMessage("I don't recognize this command... try !help", channel)

def automatedAnnoyance():
    t = threading.Timer(3600.0, automatedAnnoyance)
    t.daemon = True
    t.start()
    msg = " Automated Annoyance"
    print msg
    annoyForCRs(cHannel, False)

Initialize()
automatedAnnoyance()

while True:
    data = irc.recv(4096)
    print data
    if "ING" in data:
        rawSend("PONG")
        continue

    if "PRIVMSG " + cHannel in data:
        channelRequests(cHannel, data)
        continue
