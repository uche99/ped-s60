import os
import sys

# Application version (major, minor, build)
version = (2, 20, 0)
version_tail = 'beta'

# =====================================================================================================
# MAKE FUNCTIONS

build = '-B' in sys.argv[1:]

def make(name):
    try:
        inputs, target = makefile[name]
    except KeyError:
        return
    map(lambda x: make(x), inputs)
    if name not in makefile:
        return
    print '>', name + ':',
    failed = filter(lambda x: not os.path.exists(x), inputs)
    if failed:
        raise ValueError('missing: ' + ', '.join(failed))
    go = build
    if not go:
        if os.path.exists(name):
            tim = os.stat(name).st_mtime
            times = map(lambda x: os.stat(x).st_mtime, inputs)
            if filter(lambda x: x > tim, times):
                go = True
        else:
            go = True
    if go:
        print 'making'
        target()
        del makefile[name]
        return
    print 'nothing to do'

def listdir(name):
    return map(lambda x: os.path.join(name, x), os.listdir(name))

def system(cmds):
    for c in cmds.splitlines():
        c = c.strip()
        if not c.startswith('#'):
            print c
            os.system(c)

def verstr(ver=None, tail=None):
    if ver == None:
        ver = version
    if tail == None:
        tail = version_tail
    if tail:
        tail = '_' + tail
    return '%d.%02d%s' % (ver[:2] + (tail,))

# =====================================================================================================
# PROJECT SPECIFIC STUFF

def build_sis_pre3(ed):
    '''Creates pkg file with current version number set and creates a sis file using it.'''
    f = file('ped_%s.pkg' % ed, 'r')
    lines = f.readlines()
    f.close()
    for i in xrange(len(lines)):
        if lines[i].startswith('#{"Ped"}'):
            lines[i] = lines[i][:-9] + '%02d,%02d,%02d\n' % version
            break
    pkgname = 'Ped_%s_%s.pkg' % (verstr(), ed)
    f = file(pkgname, 'w')
    f.writelines(lines)
    f.close()
    system('makesis.exe ' + pkgname)
    os.remove(pkgname)
    sisname = pkgname[:-4] + '.sis'
    if os.path.exists(sisname):
        os.rename(sisname, sisname) # this makes the extension lower case
    else:
        raise RuntimeError('%s: makesis failed' % sisname)

# Makefile
makefile = {
    # 'dstfile': (['srcfile1', 'srcfile2'], make_function),
    'ped.mbm': (listdir('icons'),
    lambda: system('''bmconv icons\\bmconv_input_file.txt''')),
    'file_browser_icons.mbm': (listdir('file_browser_icons'),
    lambda: system('''bmconv file_browser_icons\\bmconv_input_file.txt''')),
    'ped.aif': (['ped.rss', 'ped.mbm'], lambda: system('aiftool ped ped.mbm')),
    'ped.pyo': (['ped.py'],
    lambda: system('''c:\\python22\\python -O compile.py ped.py
    copy ped.pyo system\\apps\\ped\\ped.pyc''')),
    'ui.pyo': (['ui.py'],
    lambda: system('''c:\\python22\\python -O compile.py ui.py
    copy ui.pyo system\\apps\\ped\\ui.pyc''')),
    'Ped_%s_1stEd.sis' % verstr():
    (['ped_1stEd.pkg', 'default.py', 'ped.pyo', 'ui.pyo', 'ped.aif', 'ped_1stEd.app', 'ped.rsc', 'file_browser_icons.mbm', 'LICENSE'],
    lambda: build_sis_pre3('1stEd')),
    'Ped_%s_2ndEd.sis' % verstr():
    (['ped_2ndEd.pkg', 'default.py', 'ped.pyo', 'ui.pyo', 'ped.aif', 'ped_2ndEd.app', 'ped.rsc', 'file_browser_icons.mbm', 'LICENSE'],
    lambda: build_sis_pre3('2ndEd')),
    'Ped_%s_3rdEd.sis' % verstr():
    (['default.py', 'ped.pyo', 'ui.pyo', 'file_browser_icons.mbm', 'LICENSE'],
    lambda: system('''copy default.py build_3rdEd\\
    copy ped.pyo build_3rdEd\\ped.pyc
    copy ui.pyo build_3rdEd\\ui.pyc
    copy file_browser_icons.mbm build_3rdEd\\
    copy LICENSE build_3rdEd\\
    ensymble.py py2sis --uid=0xA00042B5 --caps LocalServices+NetworkServices+ProtServ+ReadUserData+SwEvent+UserEnvironment+WriteUserData+Location+PowerMgmt+ReadDeviceData+SurroundingsDD+TrustedUI+WriteDeviceData --appname=Ped --version=%d.%02d build_3rdEd Ped_%s_3rdEd.sis''' % (version[:2] + (verstr(),))))
}

# Removes temporary developemt files
map(os.remove, listdir('system\\apps\\ped'))

# =====================================================================================================

# Make all
map(make, makefile.keys())
raw_input('Press return to quit...')
