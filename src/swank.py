import re

class SwankParser:
    def __init__(self):
        # Simplistic regexps, but does the job.
        self.wordRegexp = r"""(?s)^(?P<word>[a-zA-Z:\-]+)(?P<rest>.*)"""
        self.wsRegexp   = r"""(?s)^\s+(?P<rest>.*)"""
        self.intRegexp  = r"""(?s)^(?P<int>[0-9]+)(?P<rest>.*)"""
        self.strRegexp = r"""(?s)^"(?P<string>.*?)"(?P<rest>.*)"""

    def parse(self,stng):
        res,rest = self.parseAny(stng)
        if rest.strip() != "":
            raise RuntimeError("Swank expression could not be completely parsed.")
        return res

    def parseAny(self,stng):
        token,rest = self.nextToken(stng)
        if token == "(":
            return self.parseList(rest)
        else:
            return token,rest

    def parseList(self,stng):
        contents = []
        rest0 = stng
        while True:
            nxt,rest = self.nextToken(rest0)
            if nxt is None:
                raise RuntimeError("Closing ) expected but end of string reached.")
            if nxt == ")":
                return contents,rest
            else:
                c,rest = self.parseAny(rest0)
                rest0 = rest
                contents.append(c)

    def nextToken(self,stng):
        """Returns a pair of the next token and the remaining of the string.
           If there is no next token, returns None for the first part."""
        if len(stng) == 0:
            return None, ""
        rest = stng

        # skip whitespaces...
        while True:
            mr = re.match(self.wsRegexp, rest)
            if mr is None:
                break
            rest = mr.group("rest")
            if rest == "":
                return None, ""
        # match parentheses
        nextChar = rest[0]
        if nextChar == "(" or nextChar == ")":
            return nextChar,rest[1:]
        # match identifiers
        mr = re.match(self.wordRegexp, rest)
        if mr != None:
            w = mr.group("word")
            if w == "t":
                w = True
            elif w == "nil":
                w = False
            return w, mr.group("rest")
        # match int literals
        mr = re.match(self.intRegexp, rest)
        if mr != None:
            return int(mr.group("int")), mr.group("rest")
        # match string literals
        mr = re.match(self.strRegexp, rest)
        if mr != None:
            return mr.group("string"), mr.group("rest")
        raise RuntimeError("Cannot tokenize : %s." % rest) 
            

def main():
    parser = SwankParser()
    swankExpr = """
(:return (:ok (:pid nil :implementation (:name "ENSIME-ReferenceServer") :version "0.7.4")) 1)
"""
    rest = swankExpr
    while True:
        token,rest = parser.nextToken(rest)
        if token is None:
            break
        print "Token : %s" % token

    res = parser.parse(swankExpr)
    print res


if __name__ == "__main__":
    pass#main()
