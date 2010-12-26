from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import log
import random
import time
import sys
import re
import math
import urllib

class Tirc(irc.IRCClient):

    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def _get_com(self):
        return self.factory.com()
    com = property(_get_com)

    def signedOn(self):
        self.ident()
        log.msg("Signed on as %s" % self.nickname)

    def joined(self, channel):
        log.msg("Joined %s" % channel)
        log.msg("Got topic %s" % self.topic(channel))
        
        self.dictionary = {}
        self.BadWordC = 3

    def noticed(self, user, channel, message):
        log.msg("I got a notice from %s in %s, here it is: %s" % (user,
            channel, message))

    def ident(self):
        log.msg("Trying to ident.")
        self.msg('NickServ', 'identify %s' % self.factory.password)
        self.join(self.factory.channel)

    def privmsg(self, user, channel, msg):
        log.msg("\nUser: %s\nChannel: %s\nMessage: %s\n" % (user, channel, msg))
        #work out if its addressed to me
        chain = msg.strip()
        ifuser = user.split("!")
        log.msg(irc.IRCClient.sendLine(self,"/names #python-forum"))
        log.msg("\nifuser: %s" % ifuser)
        if ifuser[0] == "Taos" or ifuser[0] == "ghoulmaster": opuser = True
        else: opuser = False
        if re.match('.*shit.*|.*fuck.*|.*bitch.*', msg) and not opuser:
            if ifuser[0] not in self.dictionary: self.dictionary[ifuser[0]]=1
            else: self.dictionary[ifuser[0]]=self.dictionary[ifuser[0]]+1
            irc.IRCClient.msg(self, channel, "Watch your language %s, you have been warned %d times. %d time(s) = kick." % (ifuser[0], self.dictionary[ifuser[0]], self.BadWordC))
            if self.dictionary[ifuser[0]] == self.BadWordC:
                irc.IRCClient.kick(self, channel, ifuser[0], reason="Swore 3 times")
                self.dictionary[ifuser[0]]=0
#        if re.search('bun.*bot',ifuser[0]): irc.IRCClient.kick(self, channel, ifuser[0], reason="I dislike you")
        if msg.startswith(self.nickname) or msg.startswith("!"):
            if msg.startswith("!"): chain = chain.split()
            else: chain = chain.split()[1:]
            if chain[0].startswith('!'):
                chain[0].strip('!')
                log.msg("\n %s" % chain[0])
                if "kick" == chain[0] or "!kick" == chain[0]:
                    if opuser: irc.IRCClient.kick(self, channel, chain[1], reason="cuz i said so")
                    else: irc.IRCClient.kick(self, channel, ifuser[0], reason="WTF, YOU AINT OP BITCH!!") 
                elif "mode" == chain[0] or "!mode" == chain[0]:
                    if opuser:
                       isTrue = False
                       if chain[1] == "+": isTrue = True
                       else: isTrue = False 
                       irc.IRCClient.mode(self, "#python-forum", isTrue, chain[2], user=chain[3])
                    else: irc.IRCClient.kick(self, channel, ifuser[0], reason="WTF, YOU AINT OP BITCH!!")
                elif "bcount" == chain[0] or "!bcount" == chain[0]:
                    if opuser:
                        self.BadWordC = int(chain[1])
                        irc.IRCClient.msg(self, channel, "Bad word count has been changed to %d"%self.BadWordC)
                    else: irc.IRCClient.kick(self, channel, ifuser[0], reason="WTF, YOU AINT OP BITCH!!")
                else: self.msg(channel, self.com.process_command(chain, opuser))
                
            else:
                pass
        else:
            pass

    def get_topic(self):
        return """Welcome to Python-forum ~ Tenarus is a bot, powered by Tirc
        written by Taos ~ Don't ask just ask. ~ Paste > 3 lines? Use a paste
        service..."""
    
class TircFactory(protocol.ClientFactory):
    protocol = Tirc

    def __init__(self, channel, nickname, password, com_map):
        self.channel = channel
        self.nickname = nickname
        self.password = password
        self.com = com_map

    def clientConnectionLost(self, connector, reason):
        log.msg("Lost connection because: %s Reconnecting" % reason)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        log.msg("Could not connect: %s" % reason)

class COM(object):
    def __init__(self):
        self.cmds = {'!time':self.get_time,
                    '!google':self.google_search,
                    '!help':self.helper,
                    '!prime':self.prime}
        self.opcmds = {'!time':self.get_time,
                    '!google':self.google_search,
                    '!help':self.helper,
                    '!prime':self.prime, 
                    '!kick':None,
                    '!mode':None,
                    '!bcount':None}
    def process_command(self, cmds, opuser):
        self.opuser = opuser
        if cmds[0] not in self.cmds:
            return self.err1()
        cmds.append('')
        return self.cmds.get(cmds[0], self.err1)(' '.join(cmds[1:]))

    def err1(self, *args):
        return "Not a recognised cmd, type ghoulbot: !help for more info"

    def helper(self, *args):
        if self.opuser: return "Avalible cmds for op's are, %s" % self.opcmds.keys()
        else: return "Avalible cmds are, %s" % self.cmds.keys()

    def get_time(self, *args):
        return time.asctime()

    def google_search(self, *args):
        return "http://www.google.com/search?q=%s" % urllib.quote(''.join(item for item in args))


    def prime(self, *args):
        try:
            num = int(args[0])
        except ValueError:
            return "Dude.... wtf is that???"
        if num > 100000:
            return "Nooo think of ghoulmaster's poor ram"
        start = time.time()
        goal = num
        candidates = int(1.3 * goal * math.log(goal))
        prime_list = range(candidates + 1)
        high_check = int(candidates ** .5) + 1
        for i in xrange(2, high_check):
            if not prime_list[i]:
                continue
            prime_list[2 * i :: i] = [0] * (candidates / i - 1)
        prime_list[:] = [i for i in prime_list if i != 0]
        return "The %d prime is: %d: Calculated in "%(num,prime_list[goal]) + str(time.time()-start)+" seconds" 

def main(chan, nick, password, out):
    log.startLogging(out)
    reactor.connectTCP('irc.freenode.net',6667,
            TircFactory(chan, nick, password))
    reactor.run()

if __name__ in '__main__':
    chan = '#python-forum'
    nick = 'ghoulbot'#raw_input('Enter a nick: ')
    password = 'platinum'#raw_input('Enter a pass: ')
    log.startLogging(sys.stdout)
    reactor.connectTCP('irc.freenode.net',6667,
            TircFactory(chan, nick, password, COM))
    reactor.run()