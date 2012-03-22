import os
import select
import socket
import subprocess
import tempfile
import threading

from swank import SwankParser

ENSIMESERVER = "bin/server"
ENSIMEWD     = "/home/psuter/software/ensime/current/"

class EnsimeClient:
    def __init__(self,printer=None):
        self.ensimeproc = None
        self.ensimeport = None
        self.ensimeSock = None
        self.usedIDs    = set()
        self.lock       = threading.Lock()
        self.poller     = None
        self.parser     = SwankParser()
        self.DEVNULL    = open("/dev/null", "w")
        self.printer    = printer

    class SocketPoller(threading.Thread):
        def __init__(self, enclosing):
            self.ensimeSock = enclosing.ensimeSock
            self.parser     = enclosing.parser
            self.printer    = enclosing.printer
            threading.Thread.__init__(self)

        def run(self):
            while True:
                readable = []
                while readable == []:
                    # Should always be very fast...
                    readable,writable,errors = select.select([self.ensimeSock], [], [], 60)
                s = readable[0]
                msgLen = ""
                while len(msgLen) < 6:
                    chunk = self.ensimeSock.recv(6-len(msgLen))
                    if chunk == "":
                        raise RuntimeError("Socket connection to Ensime broken (read).")
                    msgLen = msgLen + chunk
                msgLen = int("0x" + msgLen, 16)
                msg = ""
                while len(msg) < msgLen:
                    chunk = self.ensimeSock.recv(msgLen-len(msg))
                    if chunk == "":
                        raise RuntimeError("Socket connection to Ensime broken (read).")
                    msg = msg + chunk
                parsed = self.parser.parse(msg)
                self.printer("From ensime %s: " % parsed)
                
                
    def freshMsgID(self):
        with self.lock:
            i = 1
            while i in self.usedIDs:
                i += 1
            self.usedIDs.add(i)
        return i

    def freeMsgID(self, i):
        with self.lock:
            self.usedIDs.remove(i)
        return

    def getDotEnsimeDirectory(self,cwd,depth=0):
        # What an ugly hack. Unfortunately, there seems to be no way
        # to check whether you have reached / in the parent chain...
        if depth > 100:
            return None
        path = os.path.abspath(cwd)
        if not os.path.isdir(path):
            raise RuntimeError("%s is not a directory." % path)
        if ".ensime" in os.listdir(path):
            return path
        parent = os.path.join(path, os.path.pardir)
        if os.access(parent, os.R_OK) and os.access(parent, os.X_OK):
            return self.getDotEnsimeDirectory(parent,depth+1)
        else:
            return None
    
    def connect(self,cwd):
        dotEnsimeDir = self.getDotEnsimeDirectory(cwd)
        if dotEnsimeDir is None:
            raise RuntimeError("Could not find '.ensime' file in any parent directory.")
        tfname = tempfile.NamedTemporaryFile(prefix="ensimeportinfo",delete=False).name
        self.ensimeproc = subprocess.Popen([ ENSIMESERVER, tfname ], cwd=ENSIMEWD, stdin=None, stdout=self.DEVNULL, stderr=self.DEVNULL, shell=False, env=None)
        print "Waiting for port info to be written..."
        ok = False
        
        while not ok:
            fh = open(tfname, 'r')
            line = fh.readline()
            if line != "":
                ok = True
                self.ensimeport = int(line.strip())
            fh.close()
        print "Ensime is communicating on port %d" % self.ensimeport
        self.ensimeSock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.ensimeSock.connect(("127.0.0.1", self.ensimeport))
        self.ensimeSock.setblocking(0)
        self.poller = self.SocketPoller(self)
        self.poller.start()
        self.swankSend("""(swank:init-project (:root-dir "%s"))""" % dotEnsimeDir)
        return

    def swankSend(self, message):
        if self.ensimeSock != None:
            mID = self.freshMsgID()
            fullMsg = "(:swank-rpc %s %d)" % (message, mID)
            msgLen = len(fullMsg)
            asHex = hex(msgLen)[2:]
            asHexPadded = (6-len(asHex))*"0" + asHex
            self.sockWrite(asHexPadded + fullMsg)
        return

    def sockWrite(self, text):
        writable = []
        while writable == []:
            # Should always be very fast...
            readable,writable,errors = select.select([], [self.ensimeSock], [], 60)
        s = writable[0]
        totalSent = 0
        textLen = len(text)
        while totalSent < textLen:
            sent = self.ensimeSock.send(text[totalSent:])
            if sent == 0:
                raise RuntimeError("Socket connection to Ensime broken (write).")
            totalSent += sent
        return
        
    def __del__(self):
        self.swankSend("(swank:shutdown-server)")
        if self.ensimeproc != None:
            self.ensimeproc.kill()
        self.ensimeport = None
        return

    def test(self):
        self.swankSend("(swank:connection-info)") 
        self.swankSend("""
(swank:init-project (:root-dir "/home/psuter/python-tests/sbtproj/"))""")
        return

def main():
    try:
        print "Creating and connecting..."

        class Printer:
            def __call__(self,arg):
                print arg

        pcb = Printer() 
        ec = EnsimeClient(pcb)
        ec.connect("/home/psuter/python-tests/sbtproj/src/main/scala/random/")
        # ec.test()
        while True:
            pass
        print "Deleting..."
        del ec
    except RuntimeError as msg:
        print "There was an error: %s" % msg

if __name__ == "__main__":
    pass#main()
