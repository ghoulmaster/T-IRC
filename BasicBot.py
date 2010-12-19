from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import log
import random
import time
import sys

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
        if msg.startswith(self.nickname):
            chain = chain.split()[1:]
            if chain[0].startswith('!'):
                chain[0].strip('!')
                self.msg(channel, self.com.process_command(chain))
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
                    '!help':self.helper}

    def process_command(self, cmds):
        if cmds[0] not in self.cmds:
            return self.err1()
        cmds.append('')
        return self.cmds.get(cmds[0], self.err1)(' '.join(cmds[1:]))

    def err1(self, *args):
        return "Not a recognised cmd, type Tenarus: !help for more info"

    def helper(self, *args):
        return "Avalible cmds are, %s" % self.cmds.keys()

    def get_time(self, *args):
        return time.asctime()

    def google_search(self, *args):
        return 'http://www.google.com/search?q=%s' % ''.join(
                [item for item in args])

def main(chan, nick, password, out):
    log.startLogging(out)
    reactor.connectTCP('irc.freenode.net',6667,
            TircFactory(chan, nick, password))
    reactor.run()

if __name__ in '__main__':
    chan = '#python-forum'
    nick = raw_input('Enter a nick: ')
    password = raw_input('Enter a pass: ')
    log.startLogging(sys.stdout)
    reactor.connectTCP('irc.freenode.net',6667,
            TircFactory(chan, nick, password, COM))
    reactor.run()
