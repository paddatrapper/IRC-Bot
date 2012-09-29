import socket, re
import chatLog

from commandModule import CommandModule
from behaviourModule import BehaviourModule

from settings import read_config

class IRCBot:
    def __init__(self, tempCacheSize=4096):
        conf = read_config()
        self.network = conf['network']
        self.port = int(conf['port'])
        self.channel = conf['channel']
        self.quitCmd = conf['quit']
        self.nickname = conf['nick']
        self.password = conf['password']
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.tempCacheSize = tempCacheSize
        self.cLog = chatLog.ChatLog()

        self.behaviourModule = BehaviourModule()
        self.commandModule = CommandModule()
        
        self.regexIsCommand = re.compile(r"(?P<command>!!..+)")
        self.regexIsChat = re.compile(r":(?P<user>\w+)!~(?P<isp>.+)\sPRIVMSG\s(?P<channel>[#\w-]+)\s:(?P<message>.+)")

    def run(self):
        self.socket.connect((self.network, self.port))
        self.log(self.socket.recv(self.tempCacheSize))
        self.socket.send('NICK %s \r\n' % self.nickname)
        self.socket.send('USER %s some stuff :Python IRC\r\n' % self.nickname)#change this
        self.socket.send('JOIN %s \r\n' % self.channel)
        
        # need to register bot nick bofre you can use this. If you'd rather skip register comment out next lines.
        self.socket.send('PRIVMSG NickServ :IDENTIFY %s %s\r\n' % (self.nickname, self.password))
        
        self.mainLoop()

    def mainLoop(self):
        while True:
            receivedData = self.socket.recv(self.tempCacheSize)
            #self.log(recievedData)
            messageInfo = dict()
            isChat = self.regexIsChat.match(receivedData)
            if isChat:
                messageInfo['user'] = isChat.group('user')
                messageInfo['isp'] = isChat.group('isp')
                messageInfo['channel'] = isChat.group('channel')
                messageInfo['message'] = isChat.group('message')

                isCommand = self.regexIsCommand.match(messageInfo['message'])
                if isCommand:
                    self.commandModule.runCommand(isCommand.group('command'), messageInfo)

            self.behaviourModule.performBehaviours(receivedData)
            
            #temporary quit method, should be changed so only admins can use
            if receivedData.find(self.quitCmd) != -1:
                self.log("Quitting")
                self.socket.send('QUIT\r\n')
                break
            
            #make sure we don't time out of server
            if receivedData.find('PING') != -1:
                self.socket.send('PONG %s \r\n' % receivedData.split()[1])
            else:
                # moved log here to filter out ping/pong chatter
                self.log(receivedData)

    def log(self, stringToLog):
        #change eventually to log in a file but for now print is fine
        print stringToLog
        self.cLog.addLog(stringToLog)

    def registerCommand(self, commandName, **options):
        def decorator(f):
            self.commandModule.commandList[commandName] = f()
            return f
        return decorator

    def registerBehaviour(self, **options):
        def decorator(f):
            self.behaviourModule.behaviourList.append(f())
            return f
        return decorator

ircBot = IRCBot()

