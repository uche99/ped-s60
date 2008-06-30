#
# make.py
#
# This file takes care of building sis files.
#

import os
import sys
import getopt

# Version (major, minor, build)
version = (2, 30, 0)
version_tail = 'beta'

# python 2.2 binary path
python22 = 'c:\\python22\\python.exe'

# 2nd edition EPOCROOT
epocroot2 = 'c:\\symbian\\7.0s\\Series60_v20_CW'

# ensymble path
ensymble = 'ensymble.py'

def main():

    # commands used in 3rd edition build, used twice later
    ped_3rded_system = '''rmdir /s/q build_3rdEd
                       mkdir build_3rdEd
                       copy default.py build_3rdEd
                       copy ped.pyo build_3rdEd\\ped.pyc
                       copy ui.pyo build_3rdEd\\ui.pyc
                       copy file_browser_icons.mif build_3rdEd
                       copy LICENSE build_3rdEd
                       mkdir build_3rdEd\\lang
                       xcopy lang build_3rdEd\\lang /s
                       %s py2sis --vendor="Arkadiusz Wahlig" --icon=ped.svg --appname=Ped --version=%d.%d.%d --verbose %%s build_3rdEd %%s''' % \
                       ((ensymble,) + version)

    # Rules
    rules = {
    
        # 'dstfile': (['srcfile1', 'srcfile2'], make_function),

        'ped.mbm': (listdir('icons\\mbm\\app'),
            lambda: system('''bmconv icons\\mbm\\app\\bmconv_input_file.txt''')),
        
        'file_browser_icons.mbm': (listdir('icons\\mbm\\file_browser'),
            lambda: system('''bmconv icons\\mbm\\file_browser\\bmconv_input_file.txt''')),
        
        'file_browser_icons.mif': (listdir('icons\\mif\\file_browser'),
            lambda: system('''mifconv file_browser_icons.mif /Ficons\\mif\\file_browser\\mifconv_input_file.txt''')),
        
        'ped.aif': (['ped.rss', 'ped.mbm'],
            lambda: system('''set PATH=%s\\Epoc32\\tools;%%PATH%%
                           aiftool ped ped.mbm''' % epocroot2)),
        
        'ped.pyo': (['ped.py'],
            lambda: system('''%s -O compile.py ped.py
                           copy ped.pyo system\\apps\\ped\\ped.pyc''' % python22)),

        'ui.pyo': (['ui.py'],
            lambda: system('''%s -O compile.py ui.py
                           copy ui.pyo system\\apps\\ped\\ui.pyc''' % python22)),
        
        'Ped_%s_2ndEd.sis' % verstr():
            (['ped_2ndEd.pkg', 'default.py', 'ped.pyo', 'ui.pyo', 'ped.aif', 'ped_2ndEd.app',
              'ped.rsc', 'file_browser_icons.mbm', 'LICENSE'],
            lambda: build_sis_pre3('2ndEd')),
        
        'Ped_%s_3rdEd_unsigned_testrange.sis' % verstr():
            (['default.py', 'ped.pyo', 'ui.pyo', 'ped.svg', 'file_browser_icons.mif', 'LICENSE'],
            lambda: system(ped_3rded_system % \
                           ('--uid=0xE111C2B6 --caps=PowerMgmt+ReadDeviceData+WriteDeviceData+TrustedUI+ProtServ+SwEvent+NetworkServices+LocalServices+ReadUserData+WriteUserData+Location+SurroundingsDD+UserEnvironment',
                           'Ped_%s_3rdEd_unsigned_testrange.sis' % verstr()))),
    
        'Ped_%s_3rdEd_no_caps.sis' % verstr():
            (['default.py', 'ped.pyo', 'ui.pyo', 'ped.svg', 'file_browser_icons.mif', 'LICENSE'],
            lambda: system(ped_3rded_system % \
                           ('--uid=0xA00042B5',
                           'Ped_%s_3rdEd_no_caps.sis' % verstr()))),

        'all': (['Ped_%s_2ndEd.sis' % verstr(),
            'Ped_%s_3rdEd_unsigned_testrange.sis' % verstr(),
            'Ped_%s_3rdEd_no_caps.sis' % verstr()],
            lambda: None),
    
    }

    # Removes temporary 2nd ed. development files
    map(os.remove, listdir('system\\apps\\ped'))

    # Parse arguments
    opts, args = getopt.gnu_getopt(sys.argv[1:], 'B')
    opts = dict(opts)
    try:
        name = args[0]
    except IndexError:
        name = 'all'
    build = '-B' in opts

    # Make
    make(rules, name, build)

def build_sis_pre3(ed):
    '''Creates pkg file with current version number set and creates a sis file using it.
    '''

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

# =====================================================================================================

def submake(rules, name, build):
    ret = False
    try:
        inputs, target = rules[name]
    except KeyError:
        return ret
    for x in inputs:
        if submake(rules, x, build):
            ret = True
    if name not in rules:
        return ret
    try:
        failed = [x for x in inputs if not os.path.exists(x)]
        if failed:
            raise ValueError('missing: ' + ', '.join(failed))
        go = build
        if not go:
            if os.path.exists(name):
                tim = os.stat(name).st_mtime
                for x in inputs:
                    if os.stat(x).st_mtime > tim:
                        go = True
                        break
            else:
                go = True
        del rules[name]
        if go:
            target()
            return True
        return ret
    except:
        print '>', name + ': failed'
        raise

def make(rules, name, build=False):
    if name not in rules:
        raise ValueError('no rule for %s' % repr(name))
    if submake(rules.copy(), name, build):
        print '>', name + ': done'
    else:
        print '>', name + ': nothing to do'

def listdir(name):
    return map(lambda x: os.path.join(name, x), os.listdir(name))

def system(cmds):
    for c in cmds.splitlines():
        c = c.strip()
        if not c.startswith('#'):
            print c
            os.system(c)

def verstr():
    if version_tail:
        tail = '_' + version_tail
    else:
        tail = ''
    return '%d.%02d.%d%s' % (version + (tail,))

if __name__ == '__main__':
    main()
