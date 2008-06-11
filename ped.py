#
# ped.py
#
# Nokia S60 on-phone Python IDE.
#
# Copyright (c) 2007-2008, Arkadiusz Wahlig
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


# application version
__version__ = '2.30 beta'


import sys
import e32
import os
import ui


symbols = [('()', 1),
           ('[]', 1),
           ('{}', 1),
           ("''", 1)]


statements = [('____', 2),
              ('break', None),
              ('class :', 6),
              ('class ():', 6),
              ('class (object):', 6),
              ('continue', None),
              ('def ():', 4),
              ('def (self):', 4),
              ('elif :', 5),
              ('else:', None),
              ('except:', None),
              ('finally:', None),
              ('for  in :', 4),
              ('from  import *', 5),
              ('global ', None),
              ('if :', 3),
              ('import ', None),
              ('lambda :', 7),
              ('pass', None),
              ('print ', None),
              ('return', None),
              ('try:', None),
              ("u''", 2),
              ('while :', 6)]


class GlobalWindowModifier(object):
    def __init__(self):
        self.control_keys += (ui.EKeyStar, ui.EKey0, ui.EKeyHash)

    def focus_changed(self, focus):
        if focus:
            try:
                wnds_item = self.menu.find(title=_('Windows'))[0]
                wnds_item.submenu = ui.screen.get_windows_menu()
                wnds_item.submenu.sort()
                wnds_item.hidden = not len(wnds_item.submenu)
                self.update_menu()
            except IndexError:
                pass

    def control_key_press(self, key):
        if key == ui.EKeyStar:
            StdIOWrapper.shell()
            return True
        elif key == ui.EKey0:
            app.runscript_click()
            return True
        elif key == ui.EKeyHash:
            app.open_click()
            return True
        return False


class RootWindow(ui.RootWindow, GlobalWindowModifier):
    def __init__(self, *args, **kwargs):
        ui.RootWindow.__init__(self, *args, **kwargs)
        GlobalWindowModifier.__init__(self)
        self.no_popup_menu = False
        self.keys += (ui.EKeySelect,)
        self.text = _(u'Version: %s\nPython for S60: %s\n') % (__version__, e32.pys60_version)
        
        # setup stdio redirection
        self.old_stdio = sys.stdin, sys.stdout, sys.stderr
        sys.stdin = sys.stdout = sys.stderr = StdIOWrapper()

    def redraw_callback(self, rect):
        ui.RootWindow.redraw_callback(self, rect)
        if len(ui.screen.windows) == 1: # if the root window is the only one
            white = 0xffffff
            f = 'dense'
            space = 8
            m = self.body.measure_text(u'A', font=f)[0]
            h = m[3]-m[1]
            x, y = 10, 10+h
            self.body.text((x, y), u'Ped - Python IDE', fill=white, font=f)
            y += space
            self.body.line((x, y, ui.layout(ui.EMainPane)[0][0]-x, y), outline=white)
            for ln in unicode(self.text).split(u'\n'):
                ln = ln.strip()
                y += space+h
                self.body.text((x, y), ln, fill=white, font=f)

    def close(self):
        r = ui.RootWindow.close(self)
        if r:
            # restore stdio redirection
            sys.stdin, sys.stdout, sys.stderr = self.old_stdio
            # exit application
            ui.app.set_exit()

    def key_press(self, key):
        if key == ui.EKeySelect:
            if self.no_popup_menu:
                return True
            menu = ui.Menu(_('File'))
            menu.append(ui.MenuItem(_('Open...'), target=app.open_click))
            def make_target(klass):
                return lambda: app.new_file(klass)
            for klass in file_windows_types:
                menu.append(ui.MenuItem(_('New %s') % klass.type_name, target=make_target(klass)))
            item = menu.popup()
            if item:
                target = item.target
                # we disable the popup menu so it can't be immediately called again
                self.no_popup_menu = True
                def do():
                    target()
                    self.no_popup_menu = False
                ui.schedule(do)
                return True
        return ui.RootWindow.key_press(self, key)

    def focus_changed(self, focus):
        GlobalWindowModifier.focus_changed(self, focus)
        ui.Window.focus_changed(self, focus)

    def control_key_press(self, key):
        if GlobalWindowModifier.control_key_press(self, key):
            return True
        return ui.Window.control_key_press(self, key)


class Window(ui.Window, GlobalWindowModifier):
    def __init__(self, *args, **kwargs):
        ui.Window.__init__(self, *args, **kwargs)
        GlobalWindowModifier.__init__(self)
        try:
            menu = ui.screen.rootwin.menu.copy()
            self.init_menu(menu)
            self.menu = menu
        except AttributeError:
            # in case shell is opened to display an error while Ped is closing
            pass

    def init_menu(self, menu):
        pass

    def close(self):
        r = ui.Window.close(self)
        if r:
            self.menu = ui.Menu()
        return r

    def focus_changed(self, focus):
        GlobalWindowModifier.focus_changed(self, focus)
        ui.Window.focus_changed(self, focus)

    def control_key_press(self, key):
        if GlobalWindowModifier.control_key_press(self, key):
            return True
        return ui.Window.control_key_press(self, key)


class TextWindow(Window):
    def __init__(self, *args, **kwargs):
        Window.__init__(self, *args, **kwargs)
        self.body = ui.Text()
        self.find_text = u''
        self.keys += (ui.EKeyEnter, ui.EKeySelect)
        self.control_keys += (ui.EKey3, ui.EKey6, ui.EKey2, ui.EKey4, ui.EKey7,
                              ui.EKeyLeftArrow, ui.EKeyRightArrow,
                              ui.EKeyUpArrow, ui.EKeyDownArrow, ui.EKeyEdit)
        self.apply_settings()

    def init_menu(self, menu):
        try:
            file_item = menu.find(title=_('File'))[0]
        except IndexError:
            return
        edit_menu = ui.Menu()
        edit_menu.append(ui.MenuItem(_('Find...'), target=self.find_click))
        edit_menu.append(ui.MenuItem(_('Find Next'), target=self.findnext_click))
        edit_menu.append(ui.MenuItem(_('Find All...'), target=self.findall_click))
        edit_menu.append(ui.MenuItem(_('Go to Line...'), target=self.gotoline_click))
        edit_menu.append(ui.MenuItem(_('Top'), target=self.move_beg_of_document))
        edit_menu.append(ui.MenuItem(_('Bottom'), target=self.move_end_of_document))
        edit_menu.append(ui.MenuItem(_('Full Screen'), target=self.fullscreen_click))
        i = menu.index(file_item)
        menu.insert(i+1, ui.MenuItem(_('Edit'), submenu=edit_menu))

    def enter_key_press(self):
        pass

    def key_press(self, key):
        if key == ui.EKeySelect:
            self.body.add(u'\n')
            ui.schedule(self.enter_key_press)
            return True
        elif key == ui.EKeyEnter:
            ui.schedule(self.enter_key_press)
            return True
        return Window.key_press(self, key)

    def control_key_press(self, key):
        if key == ui.EKey3:
            self.find_click()
            return True
        elif key == ui.EKey6:
            self.findnext_click()
            return True
        elif key == ui.EKey2:
            self.findall_click()
            return True
        elif key == ui.EKey4:
            self.gotoline_click()
            return True
        elif key == ui.EKey7:
            self.fullscreen_click()
            return True
        elif key == ui.EKeyEdit:
            item = self.menu.find(title=_('Edit'))[0].submenu.popup()
            if item:
                item.target()
        elif key == ui.EKeyLeftArrow:
            self.move_beg_of_line(1)
            self.reset_control_key()
        elif key == ui.EKeyRightArrow:
            self.move_end_of_line(-1)
            self.reset_control_key()
        elif key == ui.EKeyUpArrow:
            self.move_page_up(1)
        elif key == ui.EKeyDownArrow:
            self.move_page_down(-1)
        else:
            return Window.control_key_press(self, key)
        return False

    def apply_settings(self, font='font', color='defcolor'):
        do = False
        try:
            value = app.settings[font].get()
            if self.body.font != value:
                self.body.font = value
                do = True
        except KeyError:
            pass
        try:
            value = app.settings[color].get()
            if self.body.color != value:
                self.body.color = value
                do = True
        except KeyError:
            pass
        if do:
            pos = self.body.get_pos()
            self.body.set(self.body.get())
            self.body.set_pos(pos)

    def update_settings(cls):
        ui.screen.rootwin.focus = True
        for win in ui.screen.find_windows(TextWindow):
            win.apply_settings()
        ui.screen.rootwin.focus = False
    update_settings = classmethod(update_settings)

    def get_lines(self):
        '''returns all lines as list of (number, offset, string) tuples;
        line numbers are counted from 1, offset is counted from start of text,
        string is unicode
        '''
        lines = []
        pos = 0
        n = 1
        for line in self.body.get().split(u'\u2029'):
            lines.append((n, pos, line))
            n += 1
            pos += len(line) + 1
        return lines

    def get_line_from_pos(self, pos=None, lines=None):
        '''returns a line based on given pos (offset); a line is a tuple
        as returned by get_lines()
        '''
        if pos is None:
            pos = self.body.get_pos()
        if lines is None:
            lines = self.get_lines()
        for ln, lpos, line in lines:
            if lpos <= pos <= lpos+len(line):
                break
        return (ln, lpos, line)

    def find_click(self):
        find_text = ui.query(unicode(_('Find:')), 'text', self.find_text)
        if find_text:
            self.find_text = find_text
            self.findnext_click(False)

    def findnext_click(self, skip=True):
        find_text = self.find_text.lower()
        if not find_text:
            self.find_click()
            return
        text = self.body.get().lower()
        i = self.body.get_pos()
        while True:
            pos = i
            if skip and text[i:i+len(find_text)] == find_text:
                i += len(find_text)
            i = text.find(find_text, i)
            if i >= 0:
                self.body.set_pos(i)
            else:
                if pos != 0:
                    if ui.query(unicode(_('Not found, start from beginning?')), 'query'):
                        i = 0
                        skip = False
                        continue
                else:
                    ui.note(unicode(_('Not found')))
            break

    def findall_click(self):
        find_text = ui.query(unicode(_('Find All:')), 'text', self.find_text)
        if find_text:
            self.find_text = find_text
            find_text = find_text.lower()
            results = []
            for ln, lpos, line in self.get_lines():
                pos = 0
                while 1:
                    pos = line.lower().find(find_text, pos)
                    if pos < 0:
                        break
                    results.append((ln, lpos, line, pos))
                    pos += len(find_text)
            if results:
                win = ui.screen.create_window(FindResultsWindow,
                            title=_('Find: %s') % find_text,
                            results=results)
                line = win.modal(self)
                if line:
                    self.body.set_pos(line[1] + line[3])
            else:
                ui.note(unicode(_('Not found')))

    def gotoline_click(self):
        lines = self.get_lines()
        ln = self.get_line_from_pos(lines=lines)[0]
        ln = ui.query(unicode(_('Line (1-%d):') % len(lines)), 'number', ln)
        if ln is not None:
            if ln < 1:
                ln = 1
            ln -= 1
            try:
                self.body.set_pos(lines[ln][1])
            except IndexError:
                self.body.set_pos(self.body.len())

    def move_beg_of_line(self, delta=0):
        self.body.set_pos(self.get_line_from_pos()[1] + delta)

    def move_end_of_line(self, delta=0):
        line = self.get_line_from_pos()
        self.body.set_pos(line[1] + len(line[2]) + delta)

    def move_page_up(self, delta=0):
        lines = self.get_lines()
        i = self.get_line_from_pos(lines=lines)[0] - 1 - app.settings['pagesize'].get() + delta
        if i < 0:
            i = 0
        self.body.set_pos(lines[i][1])

    def move_page_down(self, delta=0):
        lines = self.get_lines()
        i = self.get_line_from_pos(lines=lines)[0] - 1 + app.settings['pagesize'].get() + delta
        if i >= len(lines):
            i = -1
        self.body.set_pos(lines[i][1])

    def move_beg_of_document(self):
        self.body.set_pos(0)

    def move_end_of_document(self):
        self.body.set_pos(self.body.len())

    def fullscreen_click(self):
        if self.size == ui.sizNormal:
            self.size = ui.sizLarge
        else:
            self.size = ui.sizNormal


class FindResultsWindow(Window):
    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = _('Find All')
        Window.__init__(self, *args, **kwargs)
        self.results = kwargs['results']
        self.body = ui.Listbox([(unicode(_(u'Line %d, Column %d') % (x[0], x[3])), x[2]) for x in self.results], self.select_click)
        self.menu = ui.Menu()
        self.menu.append(ui.MenuItem(_('Select'), target=self.select_click))
        self.menu.append(ui.MenuItem(_('Exit'), target=self.close))

    def close(self):
        r = Window.close(self)
        if r:
            self.menu = ui.Menu()
        return r

    def select_click(self):
        self.modal_result = self.results[self.body.current()]
        self.close()


class TextFileWindow(TextWindow):
    type_name = 'Text'
    type_ext = '.txt'
    session = ui.Settings('')

    def __init__(self, *args, **kwargs):
        TextWindow.__init__(self, *args, **kwargs)
        try:
            self.path = kwargs['path']
            text, self.encoding = self.load()
            self.fixed_encoding = True
            self.body.set(text)
            self.body.set_pos(0)
            self.title = os.path.split(self.path)[1].decode('utf8')
        except KeyError:
            self.path = None
            self.fixed_encoding = False
            self.encoding = 'latin1'
        self.control_keys += (ui.EKey9,)
        self.autosave_timer = e32.Ao_timer()
        self.apply_settings()

    def apply_settings(self, font='font', color='defcolor', defenc='defenc', autosave='autosaveinterval'):
        TextWindow.apply_settings(self, font, color)
        try:
            if not self.fixed_encoding:
                self.encoding = app.settings[defenc].get()
            autosave = app.settings[autosave].get()
            self.autosave_timer.cancel()
            if autosave and self.path is not None:
                self.autosave_timer.after(autosave, self.save)
        except AttributeError:
            pass

    def can_close(self):
        if not TextWindow.can_close(self):
            return False
        text = self.body.get()
        if self.path is None:
            if not text:
                return True
        else:
            try:
                if text == self.load()[0]:
                    return True
            except IOError:
                pass
        menu = ui.Menu(_('Changes'))
        menu.append(ui.MenuItem(_('Save'), value=True))
        menu.append(ui.MenuItem(_('Discard'), value=False))
        item = menu.popup()
        if item:
            if item.value:
                return self.save()
            else:
                return True
        return False

    def close(self):
        if TextWindow.close(self):
            self.autosave_timer.cancel()
            return True
        return False

    def init_menu(self, menu):
        TextWindow.init_menu(self, menu)
        file_menu = menu.find(title=_('File'))[0].submenu
        file_menu.append(ui.MenuItem(_('Save'), target=self.save))
        file_menu.append(ui.MenuItem(_('Save As...'), target=self.save_as))
        file_menu.append(ui.MenuItem(_('Save All'), target=self.save_all))
        file_menu.append(ui.MenuItem(_('Close'), target=self.close))
        file_menu.append(ui.MenuItem(_('Close All'), target=self.close_all))

    def control_key_press(self, key):
        if key == ui.EKey9:
            if self.save():
                ui.note(unicode(_('File saved')))
            return True
        return TextWindow.control_key_press(self, key)

    def load(self):
        if self.path is None:
            raise IOError('TextFileWindow: no path specified')
        f = file(self.path, 'r')
        text = f.read()
        f.close()
        if text.startswith('\xff\xfe') or text.startswith('\xfe\xff'):
            enc = 'utf16'
            text = text.decode(enc)
        else:
            for enc in ['utf8', 'latin1']:
                try:
                    text = text.decode(enc)
                    break
                except UnicodeError:
                    pass
            else:
                raise UnicodeError
        return text.replace(u'\r\n', u'\u2029').replace(u'\n', u'\u2029'), enc

    def save(self):
        if self.path is None:
            return self.save_as()
        autosave = app.settings['autosaveinterval'].get()
        self.autosave_timer.cancel()
        if autosave:
            self.autosave_timer.after(autosave, self.save)
        try:
            f = file(self.path, 'w')
            f.write(self.body.get().replace(u'\u2029', u'\r\n').encode(self.encoding))
            f.close()
            return True
        except IOError:
            ui.note(unicode(_('Cannot save file!')), 'error')
            return False

    def save_as(self):
        path = self.path
        if path is None:
            path = self.title.encode('utf8')
        win = ui.screen.create_window(ui.FileBrowserWindow,
                    mode=ui.fbmSave,
                    path=path,
                    title=_('Save file'))
        path = win.modal(self)
        if path is None:
            return False
        self.path = path
        self.title = os.path.split(path)[1].decode('utf8')
        return self.save()

    def close_all(self):
        ui.screen.close_windows(TextFileWindow)

    def save_all(self):
        for win in ui.screen.find_windows(TextFileWindow):
            if not win.save():
                return

    def store_session(cls):
        state = cls.session['state'].get()
        state.clear()
        for win in ui.screen.find_windows(TextFileWindow):
            try:
                text = win.body.get()
                encoding = win.encoding
                if win.load()[0] == text:
                    text = None
                else:
                    raise IOError
            except IOError:
                pass
            if win.path:
                path = win.path
            else:
                path = win.title.encode('utf8')
            state[path] = text, encoding
        cls.session.save()
    store_session = classmethod(store_session)

    def clear_session(cls):
        cls.session['state'].get().clear()
        cls.session.save()
    clear_session = classmethod(clear_session)


class AutocloseTextWindow(TextWindow):
    def focus_changed(self, focus):
        if not focus:
            self.close()


class PythonModifier(object):
    py_namespace = {}

    def py_reset_namespace(cls):
        import __main__
        cls.py_namespace.clear()
        cls.py_namespace.update(__main__.__dict__)
        cls.py_namespace.update(__main__.__builtins__.__dict__)
        cls.py_namespace['__name__'] = '__main__'
    py_reset_namespace = classmethod(py_reset_namespace)

    def _get_text(self):
        return self.body.get(), self.body.get_pos()

    def _get_objects(self, name):
        s = name.split('.')
        n = '.'.join(s[:-1])
        e = s[-1]
        if n == '':
            d = [x for x in eval('dir()', self.py_namespace) if x.startswith(e)]
            try:
                return dict([(x, eval('.'.join(s[:-1] + [x]), self.py_namespace)) for x in d])
            except:
                pass
        else:
            namespace = sys.modules.copy()
            namespace.update(self.py_namespace)
            try:
                d = [x for x in eval('dir(%s)' % n, namespace) if x.startswith(e)]
                return dict([(x, eval('.'.join(s[:-1] + [x]), namespace)) for x in d])
            except:
                pass
        return {}

    def _get_object(self, name):
        d = self._get_objects(name)
        try:
            return d[name.split('.')[-1]]
        except:
            pass

    def py_insert_indent(self):
        text, pos = self._get_text()
        pos -= 1
        i = pos - 1
        while i >= 0:
            if text[i] == u'\u2029':
                break
            i -= 1
        i += 1
        strt = i
        while i < pos and text[i].isspace():
            i += 1
        ind = i - strt
        if pos > 0 and text[pos - 1] == u':':
            ind += app.settings['indent'].get()
        self.body.add(u' ' * ind)

    def py_autocomplete(self):
        text, pos = self._get_text()
        epos = pos
        spos = pos - 1
        while spos >= 0:
            if not (text[spos].isalnum() or text[spos] in u'._'):
                break
            spos -= 1
        spos += 1
        # autocomplete should be limited to the objects starting with name
        name = text[spos:pos]
        menu = ui.Menu('%s*' % name)
        menu.items += [ui.MenuItem(title) for title in self._get_objects(name).keys()]
        menu.items += [ui.MenuItem(title, offset=off) for title, off in statements if title.startswith(name)]
        menu.sort()
        symbitems = [ui.MenuItem(title, offset=off, no_replace=True) for title, off in symbols]
        if name:
            menu.items += symbitems
        else:
            menu.items = symbitems + menu.items
        item = menu.popup(full_screen=True, search_field=True)
        if item:
            if not getattr(item, 'no_replace', False):
                # first we will remove all alnum chars following the original position
                while epos < self.body.len():
                    if not (text[epos].isalnum() or text[epos] in u'._'):
                        break
                    epos += 1
                if epos > pos:
                    self.body.delete(pos, epos - pos)
                    self.body.set_pos(pos)
            # now we will insert the new object
            ws = s = unicode(item.title)
            n = name.split(u'.')[-1]
            if s.startswith(n):
                s = s[len(n):]
            self.body.add(s)
            if hasattr(item, 'offset'): # statement, symbol
                if item.offset is not None:
                    self.body.set_pos(self.body.get_pos() - len(ws) + item.offset)

    def py_calltip(self):
        stdhelp = _('Put cursor inside argument parenthesis')
        text, pos = self._get_text()
        # search back to opening bracket
        pos -= 1
        lev = 0
        while pos >= 0:
            if text[pos] == u'(':
                lev -= 1
                if lev < 0:
                    break
            elif text[pos] == u')':
                lev += 1
            pos -= 1
        else:
            ui.note(unicode(stdhelp))
            return
        # search back to non-space chars
        while pos >= 0:
            if not text[pos].isspace():
                break
            pos -= 1
        else:
            ui.note(unicode(stdhelp))
            return
        # extract the name
        i = pos
        pos -= 1
        while pos >= 0:
            if not (text[pos].isalnum() or text[pos] in u'._'):
                break
            pos -= 1
        name = text[pos+1:i]
        if name:
            win = ui.screen.create_window(AutocloseTextWindow, title=_('Call Tip'))
            menu = ui.Menu()
            menu.append(ui.MenuItem(_('Close'), target=win.close))
            win.menu = menu
            # try to get the object
            obj = self._get_object(name)
            if obj is not None:
                # check the type of the object and try to obtain the function object
                import types
                argoffset = 0
                arg_text = ''
                if type(obj) in (types.ClassType, types.TypeType):
                    def find_init(obj):
                        try:
                            return obj.__init__.im_func
                        except AttributeError:
                            for base in obj.__bases__:
                                fob = find_init(base)
                                if fob is not None:
                                    return None
                    fob = find_init(obj)
                    if fob is None:
                        fob = lambda: None
                    else:
                        argoffset = 1
                elif type(obj) == types.MethodType:
                    fob = obj.im_func
                    argoffset = 1
                else:
                    fob = obj
                if type(fob) in (types.FunctionType, types.LambdaType):
                    try:
                        real_args = fob.func_code.co_varnames[argoffset:fob.func_code.co_argcount]
                        defaults = fob.func_defaults or []
                        defaults = list(['=%s' % repr(x) for x in defaults])
                        defaults = [''] * (len(real_args) - len(defaults)) + defaults
                        items = map(lambda arg, dflt: arg+dflt, real_args, defaults)
                        if fob.func_code.co_flags & 0x4:
                            items.append('...')
                        if fob.func_code.co_flags & 0x8:
                            items.append('***')
                        arg_text = '%s(%s)' % (name, ', '.join(items))
                    except:
                        pass
                doc = getattr(obj, '__doc__', '')
                if doc:
                    while doc[:1] in ' \t\n':
                        doc = doc[1:]
                    if not arg_text:
                        arg_text = name
                    arg_text += '\n\n' + doc
                if arg_text:
                    # display the call-tip
                    win.body.add(unicode(arg_text) + u'\n')
                else:
                    win.body.add(u'%s()\n\nNo additional info available.\n' % name)
            else:
                win.body.add(u'%s\n\nUnknown object.\n' % name)
            win.body.set_pos(0)
            win.focus = True
        else:
            ui.note(unicode(stdhelp))


PythonModifier.py_reset_namespace()


class PythonFileWindow(TextFileWindow, PythonModifier):
    type_name = 'Python'
    type_ext = '.py'

    def __init__(self, *args, **kwargs):
        TextFileWindow.__init__(self, *args, **kwargs)
        PythonModifier.__init__(self)
        self.control_keys += (ui.EKey1, ui.EKey5, ui.EKeySelect, ui.EKey8)
        self.args = u''

    def init_menu(self, menu):
        TextFileWindow.init_menu(self, menu)
        menu.insert(0, ui.MenuItem(_('Run'), target=self.run_click))
        edit_menu = menu.find(title=_('Edit'))[0].submenu
        i = edit_menu.index(edit_menu.find(title=_('Top'))[0])
        edit_menu.insert(i, ui.MenuItem(_('Code Browser'), target=self.codebrowser_click))
        edit_menu.insert(i+1, ui.MenuItem(_('Call Tip'), target=self.py_calltip))

    def enter_key_press(self):
        TextFileWindow.enter_key_press(self)
        self.py_insert_indent()

    def control_key_press(self, key):
        if key == ui.EKey1:
            self.run_click()
            return True
        elif key == ui.EKey5:
            ui.schedule(self.py_calltip)
            return True
        elif key == ui.EKeySelect:
            self.py_autocomplete()
        elif key == ui.EKey8:
            self.codebrowser_click()
            return True
        else:
            return TextFileWindow.control_key_press(self, key)
        return False

    def run_click(self):
        TextFileWindow.store_session()
        try:
            if self.load()[0] == self.body.get():
                path = self.path
            else:
                raise IOError
        except IOError:
            # save to temp file
            dirpath = 'D:\\Ped.temp'
            if not os.path.exists(dirpath):
                try:
                    os.mkdir(dirpath)
                except OSError:
                    dirpath = 'D:\\'
            path = os.path.join(dirpath, self.title.encode('utf8'))
            try:
                f = file(path, 'w')
                f.write(self.body.get().replace(u'\u2029', u'\r\n').encode(self.encoding))
                f.close()
            except IOError, (errno, errstr):
                ui.note(unicode(errstr), 'error')
                return
        if app.settings['askforargs'].get():
            menu = ui.Menu(_('Arguments'))
            if self.args:
                menu.append(ui.MenuItem(_('Last: %s') % self.args, args=self.args))
            menu.append(ui.MenuItem(_('Edit...'), args=self.args))
            menu.append(ui.MenuItem(_('No arguments'), args=u''))
            item = menu.popup()
            if not item:
                return
            if item.title.startswith('Edit'):
                args = ui.query(unicode(_('Arguments:')), 'text', item.args)
                if not args:
                    return
                item.args = args
            self.args = item.args
            args = quote_split(self.args.encode('utf8'))
        else:
            self.args = u''
            args = []
        shell = StdIOWrapper.shell()
        if shell.is_locked():
            ui.note(unicode(_('Shell is busy!')), 'error')
            return
        shell.restart()
        shell.enable_prompt(False)
        shell.lock(True)
        ui.app.menu = []
        ui.app.exit_key_handler = ui.screen.rootwin.close
        # list() will make copies so we will be able to restore these later
        mysys = list(sys.argv), list(sys.path), dict(sys.modules)
        sys.path.insert(0, os.path.split(path)[0])
        sys.argv = [path] + args
        modules = sys.modules.keys()
        try:
            execfile(path, self.py_namespace)
        except:
            value, traceback_ = sys.exc_info()[1:]
            import traceback
            traceback.print_exc()
            e = traceback.extract_tb(traceback_)[-1]
            if e[0] != path:
                s = '(%s, line ' % os.path.split(path)[1]
                value = str(value)
                pos = value.find(s, 0)
                if pos >= 0:
                    value = value[pos + len(s):]
                    self.goto_error(int(value[:value.index(')')]))
            else:
                self.goto_error(e[1], unicode(e[3]))
            del traceback_
        for m in sys.modules.keys():
            if m not in modules:
                del sys.modules[m]
        sys.argv, sys.path, sys.modules = mysys
        shell.focus = True
        shell.lock(False)
        ui.screen.redraw()
        shell.enable_prompt(True)
        TextFileWindow.clear_session()
        def remove(name):
            if os.path.isdir(name):
                for item in os.listdir(name):
                    remove(os.path.join(name, item))
                os.rmdir(name)
            else:
                os.remove(name)
        remove('D:\\Ped.temp')

    def goto_error(self, lineno, text=None):
        ln, pos, line = self.get_lines()[lineno - 1]
        if text:
            c = line.find(text)
            if c > 0:
                pos += c
        self.body.set_pos(pos)

    def codebrowser_click(self):
        tree = self.parse_code()
        def tree_to_menu(tree, title=None):
            if title is None:
                t = _('Code Browser')
            else:
                t = title
            menu = ui.Menu(t)
            for e in tree:
                if e.endswith(u'()'):
                    menu.append(ui.MenuItem(e, pos=tree[e][0]))
                    name = e[:-2]
                else: # ends with u'.'
                    name = e[:-1]
                if len(tree[e][1]):
                    if title is None:
                        t = name
                    else:
                        t = title + u'.' + name
                    menu.append(ui.MenuItem(name + u'.', submenu=tree_to_menu(tree[e][1], t)))
            menu.sort()
            return menu
        item = tree_to_menu(tree).popup(full_screen=True, search_field=True)
        if item:
            self.body.set_pos(item.pos)

    def parse_code(self):
        lines = self.get_lines()
        end = {'class' : '.', 'def' : '()'}
        last = root = {}
        lev = [(0, root)] # indent, tree
        off = 0
        for lnum, lpos, ln in lines:
            coff = off
            off += len(ln) + 1
            ln = ln.rstrip()
            t = ln.lstrip()
            if t == u'' or t[0] == u'#':
                continue
            ind = ln.find(t[0])
            t = t.split()
            if ind < lev[-1][0]:
                try:
                    while ind < lev[-1][0]:
                        lev.pop()
                except IndexError:
                    return
            elif ind > lev[-1][0]:
                lev.append((ind, last))
            if t[0] in (u'class', u'def'):
                tok = t[1].split(u'(')[0].split(u':')[0]
                name = tok + end[t[0]]
                if name in lev[-1][1]:
                    name = u'%s/%d%s' % (tok, coff + ind, end[t[0]])
                last = {}
                lev[-1][1][name] = (coff + ind, last)
        return root


class IOWindow(TextWindow):
    def __init__(self, *args, **kwargs):
        TextWindow.__init__(self, *args, **kwargs)
        self.control_keys += (ui.EKeyBackspace,)
        self.event = None
        self.locked = None
        self.write_buf = []
        def make_flusher(body, buf):
            def doflush():
                # insert the strings in place
                body.add(u''.join(buf))
                del buf[:]
                ln = body.len()
                if ln > 3000:
                    body.delete(0, ln - 250)
            return doflush
        self.do_flush = make_flusher(self.body, self.write_buf)
        self.flush_gate = e32.ao_callgate(self.do_flush)

    def control_key_press(self, key):
        if key == ui.EKeyBackspace:
            if self.locked == False:
                self.locked = True
            return True
        else:
            return TextWindow.control_key_press(self, key)

    def enter_key_press(self):
        if self.event:
            self.event.set()
            return True
        TextWindow.enter_key_press(self)
        return False

    def can_close(self):
        if self.event:
            # readline() is in progress
            self.input_aborted = True
            self.write('\n')
            self.event.set()
            return False
        if self.is_locked():
            # cause an KeyboardInterrupt in flush()
            self.locked = True
            return False
        return TextWindow.can_close(self)

    def close(self):
        r = TextWindow.close(self)
        if r:
            # explicitly delete ao_callgate object to destroy circular reference
            del self.flush_gate
        return r

    def lock(self, enable):
        if enable:
            self.locked = False
        else:
            self.locked = None

    def is_locked(self):
        return self.locked is not None

    def readline(self, size=None):
        if not e32.is_ui_thread():
            raise IOError('IOWindow.readline() called from non-UI thread')
        self.input_aborted = False
        self.event = ui.Event()
        input_pos = self.body.get_pos()
        while not self.event.isSet():
            self.event.wait()
            if not self.input_aborted and self.body.get_pos() < input_pos:
                ln = self.body.len()
                self.body.set_pos(ln)
                if input_pos > ln:
                    input_pos = self.body.get_pos()
                continue
            break
        self.event = None
        if self.input_aborted:
            raise EOFError
        text = self.body.get(input_pos).split(u'\u2029')[0].encode('latin-1', 'replace') + '\n'
        self.body.set_pos(self.body.len())
        if size and len(text) > size:
            text = text[:size]
        return text

    def write(self, s):
        try:
            self.write_buf.append(unicode(s))
        except UnicodeError:
            self.write_buf.append(s.decode('latin1'))
        self.flush()

    def writelines(self, lines):
        self.write_buf += map(unicode, lines)
        self.flush()

    def flush(self):
        if self.write_buf:
            if e32.is_ui_thread():
                self.do_flush()
            else:
                self.flush_gate()
        if self.locked == True:
            self.locked = False
            raise KeyboardInterrupt


class PythonShellWindow(IOWindow, PythonModifier):
    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = _('Python Shell')
        IOWindow.__init__(self, *args, **kwargs)
        PythonModifier.__init__(self)
        self.control_keys += (ui.EKeyUpArrow, ui.EKeyDownArrow,
                              ui.EKeyBackspace, ui.EKeyLeftArrow,
                              ui.EKey5, ui.EKeySelect)
        self.old_stdio = sys.stdin, sys.stdout, sys.stderr
        sys.stdin = sys.stdout = sys.stderr = self
        self.write('Python %s on %s\n' \
                   'Type "copyright", "credits" or "license" for more information.\n'
                   'Ped %s\n' % (sys.version, sys.platform, __version__))
        self.prompt_enabled = True
        self.init_console()
        self.prompt()

    def init_console(self):
        from code import InteractiveConsole
        self.console = InteractiveConsole(locals=self.py_namespace)
        self.history = [(u'import btconsole; btconsole.main()',)]
        self.history_ptr = len(self.history)
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = '>>> '

    def restart(self):
        PythonModifier.py_reset_namespace()
        try:
            del self.py_namespace['_']
        except KeyError:
            pass
        self.init_console()
        halfbar = '=' * 5
        self.write(halfbar + ' RESTART ' + halfbar + '\n')
        self.prompt()

    def close(self):
        r = IOWindow.close(self)
        if r:
            sys.stdin, sys.stdout, sys.stderr = self.old_stdio
        return r

    def init_menu(self, menu):
        IOWindow.init_menu(self, menu)
        menu.insert(0, ui.MenuItem(_('History'), target=self.history_click))
        file_menu = menu.find(title=_('File'))[0].submenu
        file_menu.append(ui.MenuItem(_('Export To...'), target=self.export_click))
        edit_menu = menu.find(title=_('Edit'))[0].submenu
        i = edit_menu.index(edit_menu.find(title=_('Top'))[0])
        edit_menu.insert(i, ui.MenuItem(_('Call Tip'), target=self.py_calltip))
        edit_menu.insert(i+1, ui.MenuItem(_('Clear'), target=self.clear_click))

    def control_key_press(self, key):
        if key in (ui.EKeyUpArrow, ui.EKeyDownArrow):
            if key == ui.EKeyUpArrow:
                # history back
                if self.history_ptr > 0:
                    self.history_ptr -= 1
                else:
                    ui.schedule(self.body.set_pos, self.body.get_pos())
                    return False
            else:
                # history forth
                if self.history_ptr < len(self.history):
                    self.history_ptr += 1
                else:
                    ui.schedule(self.body.set_pos, self.body.get_pos())
                    return False
            try:
                statement = self.history[self.history_ptr]
                self.body.delete(self.prompt_pos)
                self.body.set_pos(self.prompt_pos)
                self.write('\n'.join(statement))
                ui.schedule(self.body.set_pos, self.body.get_pos())
            except IndexError:
                self.body.delete(self.prompt_pos)
                ui.schedule(self.body.set_pos, self.prompt_pos)
        elif key == ui.EKeyLeftArrow:
            ln, pos, line = self.get_line_from_pos()
            if pos <= self.prompt_pos <= pos+len(line):
                pos = self.prompt_pos
            ui.schedule(self.body.set_pos, pos)
            self.reset_control_key()
        elif key == ui.EKeyBackspace:
            if not self.is_locked():
                pos = self.body.get_pos()
                if pos >= self.prompt_pos:
                    if pos == self.prompt_pos:
                        self.body.add(u' ')
                    if self.body.len() > self.prompt_pos:
                        def clear():
                            self.body.delete(self.prompt_pos)
                            self.body.set_pos(self.prompt_pos)
                        ui.schedule(clear)
                        self.reset_control_key()
            else:
                return IOWindow.control_key_press(self, key)
        elif key == ui.EKey5:
            ui.schedule(self.py_calltip)
            return True
        elif key == ui.EKeySelect:
            self.py_autocomplete()
        else:
            return IOWindow.control_key_press(self, key)
        return False

    def enable_prompt(self, enable):
        enabled = self.prompt_enabled
        self.prompt_enabled = bool(enable)
        if not enabled and enable:
            self.prompt()
        elif enabled and not enable:
            self.write('\n')

    def prompt(self):
        if not self.prompt_enabled:
            return
        try:
            self.write(str(sys.ps1))
        except:
            pass
        self.prompt_pos = self.body.get_pos()
        self.statement = []

    def enter_key_press(self):
        if IOWindow.enter_key_press(self):
            return
        if self.is_locked():
            return
        pos = self.body.get_pos()
        # remove new line character
        if pos > 0 and self.body.get(pos - 1, 1) == u'\u2029':
            self.body.delete(pos - 1, 1)
            pos -= 1
        if pos < self.prompt_pos:
            # cursor was moved before the statement start
            self.body.set_pos(self.body.len())
            if self.body.get_pos() < self.prompt_pos:
                # prompt was deleted, issue a new one
                self.write('\n')
                self.prompt()
            # recall a line
            line = self.get_line_from_pos(pos=pos)[2]
            try:
                if line.startswith(str(sys.ps1)):
                    line = line[len(str(sys.ps1)):]
            except:
                pass
            self.write(line)
            return
        if self.body.get(pos).find(u'\u2029') >= 0:
            # cursor was moved back in an multiline statement
            self.write('\n')
            self.py_insert_indent()
            return
        # cursor at the last statement line, statement execution follows
        self.body.set_pos(self.body.len())
        statement = self.body.get(self.prompt_pos).split(u'\u2029')
        self.write('\n')
        # remove empty lines so they don't break the statement
        statement = [x for x in statement[:-1] if x.strip()] + statement[-1:]
        self.lock(True)
        try:
            self.console.resetbuffer()
            more = False
            for line in statement:
                if line.strip():
                    s = line
                else:
                    s = u''
                if not self.console.push(s.encode('latin1')):
                    break
            else:
                self.py_insert_indent()
                return
            if statement[0] and self.history[-1] != tuple(statement):
                self.history.append(tuple(statement))
            self.history_ptr = len(self.history)
            self.prompt()
        finally:
            self.lock(False)

    def apply_settings(self, font='font', color='shcolor'):
        IOWindow.apply_settings(self, font, color)

    def history_click(self):
        win = ui.screen.create_window(HistoryWindow,
                    history=self.history,
                    ptr=self.history_ptr)
        ptr = win.modal(self)
        if ptr is not None:
            self.history_ptr = ptr
            statement = self.history[ptr]
            self.body.delete(self.prompt_pos)
            self.body.set_pos(self.prompt_pos)
            self.write('\n'.join(statement))

    def export_click(self):
        win = ui.screen.create_window(ui.FileBrowserWindow,
                    mode=ui.fbmSave,
                    path='PythonShell.txt',
                    title=_('Export to'))
        path = win.modal(self)
        if path is None:
            return
        try:
            f = file(path, 'w')
            f.write(self.body.get().replace(u'\u2029', u'\r\n').encode(app.settings['defenc'].get()))
            f.close()
        except IOError:
            ui.note(unicode(_('Cannot export the output!')), 'error')

    def clear_click(self):
        if ui.query(unicode(_('Clear the buffer?')), 'query'):
            self.body.clear()
            self.prompt()


class HistoryWindow(Window):
    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = _('History')
        Window.__init__(self, *args, **kwargs)
        self.history = kwargs['history']
        try:
            ptr = kwargs['ptr']
        except KeyError:
            ptr = 0
        self.body = ui.Listbox([u''], self.select_click)
        self.body.set_list(['; '.join(filter(None, [y.strip() for y in x])).replace(':;', ':') for x in self.history], ptr)
        self.menu = ui.Menu()
        self.menu.append(ui.MenuItem(_('Select'), target=self.select_click))
        self.menu.append(ui.MenuItem(_('Exit'), target=self.close))

    def close(self):
        r = Window.close(self)
        if r:
            self.menu = ui.Menu()
        return r

    def select_click(self):
        self.modal_result = self.body.current()
        self.close()


class HelpWindow(TextWindow):
    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = _('Help')
        TextWindow.__init__(self, *args, **kwargs)
        if 'text' in kwargs:
            text = unicode(kwargs['text'])
        else:
            f = file(kwargs['path'], 'r')
            text = f.read().decode('utf8')
            f.close()
        self.body.set(text.replace(u'\r\n', u'\u2029').replace(u'\n', u'\u2029'))
        self.body.set_pos(0)

    def init_menu(self, menu):
        TextWindow.init_menu(self, menu)
        menu.insert(0, ui.MenuItem(_('Topic List'), target=self.topics_click))

    def topics_click(self):
        def istopic((ln, lpos, line)):
            i = line.find(u' ')
            if i < 0:
                return False
            for c in line[:i]:
                if not (c.isdigit() or c == u'.'):
                    return False
            return True
        menu = ui.Menu(_('Topic List'))
        for ln, lpos, topic in filter(istopic, self.get_lines()):
            menu.append(ui.MenuItem(topic, line=ln, pos=lpos))
        item = menu.popup(search_field=True)
        if item:
            self.body.set_pos(item.pos)


class StdIOWrapper(object):
    singleton = None

    def __init__(self):
        assert self.singleton is None, 'only one instance of StdIOWrapper allowed'
        self.win = None
        StdIOWrapper.singleton = self

    def shell(cls):
        self = cls.singleton
        assert self, 'StdIOWrapper must be instatinated first'
        if self.win and self.win.is_alive():
            self.win.focus = True
            return self.win
        try:
            ui.screen.create_blank_window(_('Please wait...'))
            self.win = ui.screen.create_window(PythonShellWindow)
            self.win.focus = True
            return self.win
        except:
            # ui module failed, display the error using appuifw functions directly
            import traceback
            ui.app.title = u'Fatal Error'
            ui.app.screen = 'normal'
            ui.app.focus = None
            ui.app.body = ui.Text()
            lock = e32.Ao_lock()
            ui.app.exit_key_handler = lock.signal
            ui.app.menu = [(u'Exit', lock.signal)]
            ui.app.body.set(unicode(''.join(traceback.format_exception(*sys.exc_info()))))
            lock.wait()
            # restore ui module screen
            ui.screen.redraw()
            raise
    shell = classmethod(shell)

    def readline(self, size=None):
        return self.shell().readline(size)

    def write(self, s):
        return self.shell().write(s)

    def writelines(self, lines):
        return self.shell().writelines(lines)


class PluginsWindow(Window):
    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = _('Plugins')
        ui.Window.__init__(self, *args, **kwargs)
        self.plugins_path = os.path.join(app.path, 'plugins')
        self.body = ui.Listbox([(u'', u'')], self.select_click)
        self.body.bind(ui.EKeyBackspace, self.uninstall_click)
        self.menu_empty = ui.Menu()
        self.menu_empty.append(ui.MenuItem(_('Install...'), target=self.install_click))
        self.menu_empty.append(ui.MenuItem(_('Exit'), target=self.close))
        self.menu_plugins = ui.Menu()
        self.menu_plugins.append(ui.MenuItem(_('Help'), target=self.help_click))
        self.menu_plugins.append(ui.MenuItem(_('Uninstall'), target=self.uninstall_click))
        self.menu_plugins.append(ui.MenuItem(_('Install...'), target=self.install_click))
        self.menu_plugins.append(ui.MenuItem(_('Exit'), target=self.close))
        self.popup_menu_empty = ui.Menu()
        self.popup_menu_empty.append(ui.MenuItem(_('Install...'), target=self.install_click))
        self.popup_menu_plugins = ui.Menu()
        self.popup_menu_plugins.append(ui.MenuItem(_('Help'), target=self.help_click))
        self.popup_menu_plugins.append(ui.MenuItem(_('Uninstall'), target=self.uninstall_click))
        self.update()

    def update(self):
        plugins = []
        if os.path.exists(self.plugins_path):
            for name in os.listdir(self.plugins_path):
                path = os.path.join(self.plugins_path, name)
                f = file(os.path.join(path, 'manifest.txt'))
                plugins.append((path, parse_manifest(f.read().decode('utf8'))))
                f.close()
        if plugins:
            plugins.sort(lambda a, b: -(a[1]['name'].lower() < b[1]['name'].lower()))
            lst = [(x[1]['name'],
                    unicode(_(u'Version: %s') % x[1]['version'])) for x in plugins]
            self.menu = self.menu_plugins
            self.popup_menu = self.popup_menu_plugins
        else:
            lst = [(unicode(_(u'(no plugins)')), u'')]
            self.menu = self.menu_empty
            self.popup_menu = self.popup_menu_empty
        self.body.set_list(lst, 0)
        self.plugins = plugins

    def select_click(self):
        item = self.popup_menu.popup()
        if item:
            item.target()

    def help_click(self):
        path, manifest = self.plugins[self.body.current()]
        bwin = ui.screen.create_blank_window(_('Please wait...'))
        path = os.path.join(path, 'help')
        helpfile = os.path.join(path, app.settings['language'].get())
        if not os.path.exists(helpfile):
            helpfile = os.path.join(path, 'English')
        try:
            win = ui.screen.create_window(HelpWindow,
                    path=helpfile,
                    title=_('Help for %s') % manifest['name'])
            win.body.add((u'%s\n' + _(u'Version: %s') + u'\n\n') % (manifest['name'], manifest['version']))
            win.body.set_pos(0)
            win.focus = True
        except IOError:
            ui.note(unicode(_('Cannot load help file!')), 'error')
            bwin.close()

    def install_click(self):
        win = ui.screen.create_window(ui.FileBrowserWindow, title=_('Install plugin'))
        path = win.modal(self)
        if path:
            self.install(path)

    def uninstall_click(self):
        try:
            self.uninstall(self.plugins[self.body.current()][0])
        except IndexError:
            pass

    def install(self, filename):
        import zipfile
        # plugin must be a zip file
        if not zipfile.is_zipfile(filename):
            ui.note(unicode(_('Not a plugin file!')), 'error')
            return
        z = zipfile.ZipFile(filename)
        lst = [x.lower() for x in z.namelist()]
        # plugin must contain the manifest and default python files
        if 'manifest.txt' not in lst or ('default.py' not in lst and 'default.pyc' not in lst):
            ui.note(unicode(_('Not a plugin file!')), 'error')
            return
        # parse manifest and check mandatory fields
        dct = dict([(x.lower(), x) for x in z.namelist()])
        manifest = parse_manifest(z.read(dct['manifest.txt']).decode('utf8'))
        for field in ('folder', 'name', 'version', 'ped-version-min', 'ped-version-max'):
            if field not in manifest:
                ui.note(unicode(_('%s field missing from manifest!') % field.capitalize()))
                return
        if not ui.query(unicode(_('Install\n%s %s?') % (manifest['name'], manifest['version'])), 'query'):
            return
        if __version__ < manifest['ped-version-min']:
            ui.note(unicode(_('Requires Ped in at least version %s! Your is %s.') % (manifest['ped-version-min'], __version__)), 'error')
            return
        if __version__ > manifest['ped-version-max']:
            if not ui.query(unicode(_('Supports Ped up to version %s. Your is %s. Continue?') % (manifest['ped-version-max'], __version__)), 'query'):
                return
        # create plugins directory if needed
        if not os.path.exists(self.plugins_path):
            os.mkdir(self.plugins_path)
        path = os.path.join(self.plugins_path, manifest['folder'])
        if os.path.exists(path):
            fh = file(os.path.join(path, 'manifest.txt'))
            old_manifest = parse_manifest(fh.read())
            fh.close()
            if not ui.query(unicode(_('Replace version %s with %s?') % (old_manifest['version'], manifest['version'])), 'query'):
                return
            self.uninstall(path, quiet=True)
        # create plugin directory
        os.mkdir(path)
        # extract plugin files to plugin directory
        for f in z.infolist():
            p = os.path.join(path, f.filename.replace('/', '\\'))
            if f.filename.endswith('/'):
                os.mkdir(p)
            else:
                fh = file(p, 'wb')
                fh.write(z.read(f.filename))
                fh.close()
        z.close()
        ui.note(unicode(_('%s %s installed.') % (manifest['name'], manifest['version'])), 'conf')
        ui.note(unicode(_('Restart Ped for the changes to take effect.')))
        self.update()

    def uninstall(self, path, quiet=False):
        fh = file(os.path.join(path, 'manifest.txt'))
        manifest = parse_manifest(fh.read())
        fh.close()
        if not quiet and not ui.query(unicode(_('Uninstall\n%s %s?') % (manifest['name'], manifest['version'])), 'query'):
            return
        def deldir(path):
            for name in os.listdir(path):
                filename = os.path.join(path, name)
                if os.path.isdir(filename):
                    deldir(filename)
                else:
                    os.remove(filename)
            os.rmdir(path)
        deldir(path)
        if not quiet:
            ui.note(unicode(_('%s %s uninstalled.') % (manifest['name'], manifest['version'])), 'conf')
            ui.note(unicode(_('Restart Ped for the changes to take effect.')))
        self.update()


class Application(object):
    def __init__(self):
        # path to application data
        self.path = os.path.split(sys.argv[0])[0]

        # setup i18n
        path = os.path.join(self.path, 'lang\\ped')
        try:
            alllanguages = [x.decode('utf8') for x in os.listdir(path)]
        except OSError:
            alllanguages = []
        alllanguages.append(u'English')
        alllanguages.sort(lambda a, b: -(a.lower() < b.lower()))
        # we have to load the language setting first; the real settings object
        # we will use in the app will be created later
        settings = ui.Settings(os.path.join(self.path, 'settings.bin'))
        settings.add_setting('default', 'language', ui.ComboSetting('Language', u'English', alllanguages))
        settings.load_if_available()
        self.language = settings['language'].get()
        if self.language != u'English':
            try:
                # load the ped language file
                translator.load(os.path.join(path, self.language.encode('utf8')))
            except IOError:
                pass
            try:
                # load the ui language file
                path = os.path.join(self.path, 'lang\\ui')
                ui.translator.load(os.path.join(path, self.language.encode('utf8')))
            except IOError:
                pass

        # setup settings
        allfonts = ui.available_text_fonts()
        if u'LatinBold12' in allfonts:
            defaultfont = u'LatinBold12'
        else:
            defaultfont = allfonts[0]
        allcolors = ((_('Black'), 0x000000), (_('Red'), 0x990000), (_('Green'), 0x008800), (_('Blue'), 0x000099), (_('Purple'), 0x990099))
        allorientations = [(_('Automatic'), ui.oriAutomatic)]
        if e32.s60_version_info >= (3, 0):
            allorientations += [(_('Portrait'), ui.oriPortrait), (_('Landscape'), ui.oriLandscape)]
        settings = ui.Settings(os.path.join(self.path, 'settings.bin'), title=_('Settings'))
        settings.add_category('view', ui.Category(_('View')))
        settings.add_category('text', ui.Category(_('Text')))
        settings.add_category('file', ui.Category(_('File')))
        settings.add_category('misc', ui.Category(_('Misc')))
        settings.add_setting('view', 'language', ui.ComboSetting(_('Language'), u'English', alllanguages))
        settings.add_setting('view', 'font', ui.ComboSetting(_('Text font'), defaultfont, allfonts))
        # 'color', 'shellcolor', 'orientation' and 'autosave' IDs used old ValueComboSetting class
        # and cannot be used with the new one
        settings.add_setting('view', 'defcolor', ui.ValueComboSetting(_('Editor color'), 0x000099, allcolors))
        settings.add_setting('view', 'shcolor', ui.ValueComboSetting(_('Shell color'), 0x008800, allcolors))
        settings.add_setting('view', 'scrorientation', ui.ValueComboSetting(_('Orientation'), allorientations[0][1], allorientations))
        settings.add_setting('text', 'pagesize', ui.NumberSetting(_('Page size'), 8, vmin=1, vmax=32))
        settings.add_setting('text', 'indent', ui.NumberSetting(_('Indentation size'), 4, vmin=1, vmax=8))
        settings.add_setting('file', 'defenc', ui.ComboSetting(_('Default encoding'), 'utf-8', ('ascii', 'latin-1', 'utf-8', 'utf-16')))
        settings.add_setting('file', 'autosaveinterval', ui.ValueComboSetting(_('Autosave'), 0, ((_('Off'), 0), (_('%d sec') % 30, 30), (_('%d min') % 1, 60), (_('%d min') % 2, 120), (_('%d min') % 5, 300), (_('%d min') % 10, 600))))
        settings.add_setting('misc', 'askforargs', ui.BoolSetting(_('Ask for arguments'), False))
        self.settings = settings

        # setup file browser
        ui.FileBrowserWindow.private_path = self.path
        ui.FileBrowserWindow.add_link('C:\\Python')
        ui.FileBrowserWindow.add_link('E:\\Python')
        if not ui.FileBrowserWindow.add_link('E:\\System\\Apps\\Python', _('Python Shell')):
            ui.FileBrowserWindow.add_link('C:\\System\\Apps\\Python', _('Python Shell'))

        # setup session
        session = ui.Settings(os.path.join(self.path, 'session.bin'))
        session.add_setting('default', 'state', ui.Setting('Files', {}))
        TextFileWindow.session = session

        # properties initialization
        self.browser_win = self.help_win = self.plugins_win = None
        self.unnamed_count = 1

    def start(self):
        # load settings
        self.settings.load_if_available()

        # setup paths
        for path in ('C:\\Python\\lib', 'E:\\Python\\lib'):
            if os.path.exists(path):
                sys.path.append(path)

        # create root ui window (desktop)
        ui.screen.create_window(RootWindow)

        # setup main menu
        file_menu = ui.Menu()
        file_menu.append(ui.MenuItem(_('New'), target=self.new_click))
        file_menu.append(ui.MenuItem(_('Open...'), target=self.open_click))
        main_menu = ui.Menu()
        main_menu.append(ui.MenuItem(_('File'), submenu=file_menu))
        main_menu.append(ui.MenuItem(_('Windows'), submenu=ui.Menu(), hidden=True))
        main_menu.append(ui.MenuItem(_('Python Shell'), target=StdIOWrapper.shell))
        main_menu.append(ui.MenuItem(_('Run Script...'), target=self.runscript_click))
        main_menu.append(ui.MenuItem(_('Settings'), target=self.settings_click))
        main_menu.append(ui.MenuItem(_('Plugins'), target=self.plugins_click))
        main_menu.append(ui.MenuItem(_('Help'), target=self.help_click))
        # BEG: temporary
        m = ui.Menu()
        m.append(ui.MenuItem('ui', target=lambda: ui.translator.save(os.path.join(self.path, 'lang-ui'))))
        m.append(ui.MenuItem('ped', target=lambda: translator.save(os.path.join(self.path, 'lang-ped'))))
        main_menu.append(ui.MenuItem(_('Dump lang'), submenu=m))
        # END: temporary
        main_menu.append(ui.MenuItem(_('Exit'), target=ui.screen.rootwin.close))
        ui.screen.rootwin.menu = main_menu

        # load and apply settings
        self.settings.load_if_available()
        self.apply_settings()

        # start plugins
        ui.schedule(self.start_plugins)

        # restore session
        TextFileWindow.session.load_if_available()
        state = TextFileWindow.session['state'].get()
        if state and ui.query(unicode(_('Last Ped session crashed. Reload its last state?')), 'query'):
            for path, (text, encoding) in state.items():
                if text is None:
                    self.load_file(path)
                else:
                    ext = os.path.splitext(path)[1].lower()
                    try:
                        klass = file_windows_types[[x.type_ext.lower() for x in file_windows_types].index(ext)]
                    except ValueError:
                        klass = TextFileWindow
                    ui.screen.create_blank_window(_('Please wait...'))
                    win = ui.screen.create_window(klass,
                        title=os.path.split(path)[1].decode('utf8'))
                    if win:
                        win.body.set(text)
                        win.body.set_pos(0)
                        win.encoding = encoding
                        if os.path.split(path)[0]:
                            win.path = path
                            win.fixed_encoding = True
                        else:
                            win.fixed_encoding = False
                        win.focus = True
        state.clear()
        try:
            TextFileWindow.session.save()
        except IOError:
            ui.note(unicode(_('Cannot update session file!')), 'error')

        # the ui is set up now so we can simply leave and the launchpad will keep us
        # running until appuifw.app.set_exit() is called (see: RootWindow.close)

    def start_plugins(self):
        plugins_path = os.path.join(self.path, 'plugins')
        if os.path.exists(plugins_path):
            slen = len(self.settings)
            for name in os.listdir(plugins_path):
                path = os.path.join(plugins_path, name)
                t = os.path.join(path, 'default.py')
                if os.path.exists(t):
                    filename = t
                else:
                    filename = os.path.join(path, 'default.pyc')
                # list() will make copies so we will be able to restore these later
                mysys = list(sys.argv), list(sys.path)
                sys.path.insert(0, os.path.split(filename)[0])
                sys.argv = [filename]
                try:
                    import __main__
                    ns = {}
                    ns.update(__main__.__dict__)
                    ns.update(__main__.__builtins__.__dict__)
                    ns['__name__'] = '__main__'
                    execfile(filename, ns)
                except:
                    from traceback import print_exc
                    print_exc()
                sys.argv, sys.path = mysys
            if len(self.settings) != slen:
                # plugins have added/removed the settings;
                # reload so the new settings are loaded too
                self.settings.load_if_available()
                self.apply_settings()
            ui.screen.redraw()

    def new_file(self, klass):
        title = 'Unnamed%d%s' % (self.unnamed_count, klass.type_ext)
        self.unnamed_count += 1
        win = ui.screen.create_window(klass,
                title=title)
        win.focus = True
        return win

    def settings_click(self):
        if self.settings.edit():
            self.apply_settings()

    def apply_settings(self):
        TextWindow.update_settings()
        for win in ui.screen.find_windows(Window):
            win.orientation = self.settings['scrorientation'].get()
        if self.settings['language'].get() != self.language:
            self.language = self.settings['language'].get()
            if self.language == u'English':
                translator.unload()
            else:
                translator.load(os.path.join(self.path, 
                    'lang\\ped\\%s' % self.language.encode('utf8')))
            ui.screen.redraw()

    def plugins_click(self):
        if self.plugins_win and self.plugins_win.is_alive():
            self.plugins_win.focus = True
            return
        self.plugins_win = ui.screen.create_window(PluginsWindow)
        self.plugins_win.focus = True

    def help_click(self):
        if self.help_win and self.help_win.is_alive():
            self.help_win.focus = True
            return
        bwin = ui.screen.create_blank_window(_('Please wait...'))
        path = os.path.join(self.path, 'lang\\help')
        helpfile = os.path.join(path, self.language.encode('utf8'))
        if not os.path.exists(helpfile):
            helpfile = os.path.join(path, 'English')
        try:
            self.help_win = ui.screen.create_window(HelpWindow,
                    path=helpfile)
            self.help_win.body.add(u'Ped - Python IDE\n'
                                   u'Version: %s\n'
                                   u'\n'
                                   u'Copyright \u00a9 2007-2008\nArkadiusz Wahlig\n'
                                   u'<arkadiusz.wahlig@gmail.com>\n'
                                   u'\n' % __version__)
            self.help_win.body.set_pos(0)
            self.help_win.focus = True
        except IOError:
            ui.note(unicode(_('Cannot load help file!')), 'error')
            bwin.close()

    def new_click(self):
        menu = ui.Menu(_('New'))
        for klass in file_windows_types:
            menu.append(ui.MenuItem(klass.type_name, klass=klass))
        item = menu.popup()
        if item:
            self.new_file(item.klass)

    def open_click(self):
        if self.browser_win:
            ui.note(unicode(_('File browser already in use!')), 'error')
            return
        self.browser_win = ui.screen.create_window(ui.FileBrowserWindow,
                title=_('Open file'))
        path = self.browser_win.modal()
        self.browser_win = None
        if not path:
            return
        self.load_file(path)

    def load_file(self, path):
        # check if this file isn't already opened
        for win in ui.screen.find_windows(TextFileWindow):
            if win.path == path:
                win.focus = True
                return
        ext = os.path.splitext(path)[1].lower()
        try:
            klass = file_windows_types[[x.type_ext.lower() for x in file_windows_types].index(ext)]
        except ValueError:
            klass = TextFileWindow
        wwin = ui.screen.create_blank_window(_('Please wait...'))
        try:
            win = ui.screen.create_window(klass,
                    path=path)
            win.focus = True
        except IOError:
            win = None
            ui.note(unicode(_('Cannot load %s file!') % os.path.split(path)[1]), 'error')
            wwin.close()
        return win

    def runscript_click(self):
        if self.browser_win:
            ui.note(unicode(_('File browser already in use!')), 'error')
            return
        self.browser_win = ui.screen.create_window(ui.FileBrowserWindow,
                title=_('Run script'))
        path = self.browser_win.modal()
        self.browser_win = None
        if not path:
            return
        if self.settings['askforargs'].get():
            menu = ui.Menu(_('Arguments'))
            menu.append(ui.MenuItem(_('Edit...')))
            menu.append(ui.MenuItem(_('No arguments')))
            item = menu.popup()
            if not item:
                return
            if item.name == 'edit':
                args = ui.query(unicode(_('Arguments:')), 'text')
                if not args:
                    return
            else:
                args = u''
            args = quote_split(args.encode('utf8'))
        else:
            args = []
        shell = StdIOWrapper.shell()
        if shell.is_locked():
            ui.note(unicode(_('Shell is busy!')), 'error')
            return
        shell.restart()
        shell.enable_prompt(False)
        shell.lock(True)
        TextFileWindow.store_session()
        ui.app.menu = []
        ui.app.exit_key_handler = ui.screen.rootwin.close
        # list() will make copies so we will be able to restore these later
        mysys = list(sys.argv), list(sys.path)
        sys.path.insert(0, os.path.split(path)[0])
        sys.argv = [path] + args
        modules = sys.modules.keys()
        try:
            execfile(path, shell.py_namespace)
        finally:
            for m in sys.modules.keys():
                if m not in modules:
                    del sys.modules[m]
            sys.argv, sys.path = mysys
            TextFileWindow.clear_session()
            shell.focus = True
            shell.lock(False)
            ui.screen.redraw()
            shell.enable_prompt(True)


def quote_split(s):
    # like s.split() but sentences in quotes
    # are treated as one word
    s += ' '
    ret = []
    for x in s.split('"'):
        i = s.index(x)
        try:
            if s[i-1] == '"' and s[i+len(x)] == '"':
                ret.append(x)
                s = s[:i-1] + s[i+len(x)+1:]
                continue
        except IndexError:
            pass
        ret += x.split()
        s = s[:i] + s[i+len(x):]
    return ret


def parse_manifest(manifest):
    # parses plugins manifest files and returns
    # their contents as dictionaries
    fields = {}
    lines = manifest.splitlines()
    lines.reverse()
    while True:
        try:
            ln = lines.pop()
        except IndexError:
            break
        p = ln.find(':')
        assert p > 0, 'mangled manifest file'
        name = ln[:p].strip().lower()
        value = []
        vln = ln[p+1:].strip()
        while vln.endswith('\\'):
            value.append(vln[:-1].strip())
            try:
                ln = lines.pop()
            except IndexError:
                break
            vln = ln.strip()
        value.append(vln)
        assert name not in fields, 'manifest field defined twice'
        fields[name] = '\n'.join(value)
    return fields


def repattr(obj, name, value):
    '''Sets an attribute of a class/object. Returns the old value.'''
    old = getattr(obj, name)
    setattr(obj, name, value)
    return old


# i18n object
translator = _ = ui.Translator()


# Supported file types
file_windows_types = [TextFileWindow, PythonFileWindow]


# Application object
app = Application()
