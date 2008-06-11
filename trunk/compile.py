#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys
import py_compile

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: compile.py <file.py>')
    py_compile.compile(sys.argv[1])
