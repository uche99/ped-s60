import sys, os
import zipfile
from optparse import OptionParser

# full path to python 2.2 binary
python22 = 'C:\\Python22\\python.exe'

__version__ = '1.00.0'

class Manifest(object):
    def __init__(self, filename=None):
        self.fields = {}
        if filename is not None:
            self.load(filename)
        
    def parse(self, data):
        lines = data.decode('utf8').splitlines()
        lines.reverse()
        self.fields = {}
        while True:
            try:
                ln = lines.pop()
            except IndexError:
                break
            try:
                p = ln.index(u':')
            except ValueError:
                raise ValueError('mangled manifest file')
            name = ln[:p].strip().title()
            value = []
            vln = ln[p+1:].strip()
            while vln.endswith(u'\\'):
                value.append(vln[:-1].strip())
                try:
                    ln = lines.pop()
                except IndexError:
                    break
                vln = ln.strip()
            else:
                value.append(vln)
            if name in self.fields:
                raise ValueError('manifest field defined twice')
            self.fields[name] = u'\r\n'.join(value)
    
    def dump(self):
        lines = []
        for name, value in self.fields.items():
            lines.append(u'%s: %s\r\n' % (name.title(), '\\\r\n'.join(value.split('\n'))))
        return (''.join(lines)).encode('utf8')

    def load(self, filename):
        f = open(filename, 'r')
        try:
            self.parse(f.read())
        finally:
            f.close()

    def save(self, filename):
        f = open(filename, 'w')
        try:
            f.write(self.dump())
        finally:
            f.close()

    def get(self, name, default=None):
        return self.fields.get(name.title(), default)

    def keys(self):
        return self.fields.keys()
        
    def items(self):
        return self.fields.items()
        
    def values(self):
        return self.fields.values()

    def clear(self):
        self.fields = {}

    def __getitem__(self, name):
        return self.fields[name.title()]
    
    def __setitem__(self, name, value):
        self.fields[name.title()] = value

    def __delitem__(self, name):
        del self.fields[name.title()]
        
    def __len__(self):
        return len(self.fields)
        
    def __contains__(self, name):
        return name.title() in self.fields

def is_best_py(path):
    # check if the given Python file path is the best one available
    base = os.path.splitext(path)[0]
    mtime = 0.0
    best = path
    for ext in ('.py', '.pyc', '.pyo'):
        p = base+ext
        if not os.path.exists(p):
            continue
        if os.path.getmtime(p) > mtime:
            mtime = os.path.getmtime(p)
            best = p
    return path.lower() == best.lower()

def archive(z, path, arcpath=None):
    if arcpath is None:
        arcpath = ''
    for name in os.listdir(path):
        if name == '.svn':
            # skip SVN directories
            continue
        fullname = os.path.join(path, name)
        arcfullname = os.path.join(arcpath, name)
        if os.path.isdir(fullname):
            archive(z, fullname, arcfullname)
        elif os.path.isfile(fullname):
            if os.path.splitext(name)[-1].lower().startswith('.py'): # *.py, *.pyc, *.pyo
                # choose best Python file
                if not is_best_py(fullname):
                    continue
                if arcfullname.lower().endswith('.pyo'):
                    arcfullname = arcfullname[:-1]+'c'
            z.write(fullname, arcfullname)

def main():
    parser = OptionParser(usage='%prog [options] plugin_dir ...',
        version='%%prog %s' % __version__)
    options, args = parser.parse_args()
    
    if not args:
        parser.error('specify plugin directory')
    
    for path in args:
        print 'Scanning "%s" directory...' % path
        
        try:
            manifest = Manifest(os.path.join(path, 'manifest.txt'))
        except IOError, err:
            sys.exit('could not load manifest: %s' % err)
        
        for field in ('Package', 'Name', 'Version', 'Ped-Version-Min', 'Ped-Version-Max'):
            if field not in manifest:
                sys.exit('manifest mandatory field missing: %s' % field)

        print 'Found "%s" plugin, version %s.' % (manifest['Name'], manifest['Version'])

        if python22:
            # compile all Python files in the plugin directory
            os.system('%s -O %s "%s"' % (python22,
                os.path.join(os.path.split(python22)[0], 'lib\\compileall.py'),
                path))

        name = 'ped_%s_%s.zip' % (manifest['Package'], manifest['Version'])
        
        try:
            z = zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED)
            archive(z, path)
            z.close()
        except Exception, err:
            sys.exit('could not archive: %s' % err)
            
        print 'Saved as "%s".' % name

if __name__ == '__main__':
    main()
    