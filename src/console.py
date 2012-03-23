import cmd

from ensime import EnsimeClient

class Console(cmd.Cmd):
    """ This class is useful to play with the Ensime server. You can use it to send Swank commands and watch the output."""
    def __init__(self,ensimeclient,printer):
        cmd.Cmd.__init__(self)
        self.completekey = None
        self.ensimeclient = ensimeclient
        self.printer      = printer
        self.prompt       = "swank> "

    def emptyline(self):
        pass
    
    def do_connect(self, line):
        self.ensimeclient.connect(line)

    def do_EOF(self, line):
        del self.ensimeclient
        return True

    def do_send(self, line):
        self.ensimeclient.swankSend(line)

    

def main():
    class Printer:
        def out(self,arg):
            print "[out] %s" % arg
        
        def err(self,arg):
            print "[err] %s" % arg

    printer = Printer()
    ensime = EnsimeClient(printer)
    console = Console(ensime,printer)
    
    console.cmdloop()     
    

if __name__ == "__main__":
    main()
