#
# create_lang_from_py.py
#
# This script parses a *.py file (give it as argument) and prints out all
# _(...) calls in the form ready to be used as a translation file.
#

import sys, os

class Translator(object):
    def __init__(self, filename=None):
        self.translations = {}
        if filename:
            self.load(filename)

    def load(self, filename):
        f = open(filename)
        self.translations = {}
        for ln in f.readlines():
            ln = ln.strip()
            if not ln or ln.startswith('#'):
                continue
            try:
                x = eval('{\n%s\n}' % ln)
            except:
                raise ValueError('%s: syntax error' % repr(ln))
            if x:
                dst = x.values()[0]
                if dst:
                    if isinstance(dst, str):
                        dst = dst.decode('latin1')
                    elif not isinstance(dst, unicode):
                        raise TypeError('translation file must contain strings only')
                    self.translations[x.keys()[0]] = dst
        f.close()

    def unload(self):
        self.translations = {}

    def __getitem__(self, name):
        return self.translations[name]
        
    def __call__(self, *strings):
        for s in strings:
            try:
                return self.translations[s]
            except KeyError:
                pass
        return unicode(strings[-1])

def parse(data):
    strings = set()
    i = 0
    while True:
        i = data.find('_(', i)
        if i < 0:
            break
        if i > 0 and (data[i-1].isalnum() or data[i-1] in '_'):
            i += 1
            continue
        start = i
        i += 2
        lev = 1
        while lev:
            if data[i] == '(':
                lev += 1
            elif data[i] == ')':
                lev -= 1
            i += 1
        strings.add(str(eval(data[start+2:i-1])))
    s = list(strings)
    s.sort()
    return s

if __name__ == '__main__':
    try:
        pyfile = sys.argv[1]
    except IndexError:
        sys.exit('Pass a *.py file as argument')
        
    try:
        trfile = sys.argv[2]
    except IndexError:
        trfile = None
        
    translator = Translator(trfile)
    
    print '# Strings from:', os.path.split(pyfile)[-1]
    print
    
    f = open(pyfile, 'rb')
    data = f.read()
    f.close()
    
    strings = parse(data)

    maxlen = 0
    for s in strings:
        maxlen = max(maxlen, len(repr(s)))
    for s in strings:
        v = translator(s)
        if v == s:
            v = u''
        print '%s%s: %s' % (repr(s), ' '*(maxlen-len(repr(s))), repr(v))
        
