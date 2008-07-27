#
# make_lang.py
#
# Parses Python source files and generates a Ped language file out of
# _(...) calls.
#
# Copyright (c) 2008, Arkadiusz Wahlig
# <arkadiusz.wahlig@gmail.com>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of Arkadiusz Wahlig nor the names of its contributors may
#   be used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from optparse import OptionParser
import sys, os

__version__ = '1.00.0'

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

    def load_if_available(self, filename):
        try:
            self.load(filename)
        except IOError:
            pass

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

def main():
    parser = OptionParser(usage='%prog [options] lang_file py_file ...',
        version='%%prog %s' % __version__)
    options, args = parser.parse_args()
    
    if len(args) < 2:
        parser.error('required arguments missing')
    elif len(args) > 2:
        parser.error('unexpected arguments')

    trfile = args[0]
    pyfile = args[1]

    translator = Translator()
    translator.load_if_available(trfile)
    
    f = open(pyfile, 'rb')
    data = f.read()
    f.close()
    
    strings = parse(data)

    sys.stdout = open(trfile, 'w')

    print '# Strings from:', os.path.split(pyfile)[-1]
    print

    maxlen = 0
    for s in strings:
        maxlen = max(maxlen, len(repr(s)))
    for s in strings:
        v = translator(s)
        if v == s:
            v = u''
        print '%s%s: %s' % (repr(s), ' '*(maxlen-len(repr(s))), repr(v))
    
    depr = []
    for s in translator.translations:
        if s in strings:
            continue
        depr.append(s)
    if depr:
        depr.sort()
        print
        print '# Deprecated strings'
        for s in depr:
            v = translator(s)
            print '%s%s: %s' % (repr(s), ' '*(maxlen-len(repr(s))), repr(v))

    sys.stdout.close()
    
if __name__ == '__main__':
    main()
