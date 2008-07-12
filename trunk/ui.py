#
# ui.py
#
# This module provides an abstraction layer for the PyS60 appuifw module.
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


import os
import e32
from appuifw import *
from key_codes import *


# platform independant reset_inactivity()
try:
    reset_inactivity = e32.reset_inactivity
except AttributeError:
    try:
        # use miso module if available
        from miso import reset_inactivity
    except ImportError:
        # no reset_inactivity() available
        reset_inactivity = lambda: None


# for 3rd edition, the InfoPopup class isn't in appuifw.__all__
# so we have to import it separately
try:
    from appuifw import InfoPopup
except ImportError:
    pass
    

# threading.Event alike class built around e32.Ao_lock
class Event(object):
    def __init__(self):
        self.lock = e32.Ao_lock()
        self.clear()

    def wait(self):
        if not self.isSet():
            self.lock.wait()

    def set(self):
        self.lock.signal()
        self.signaled = True

    def clear(self):
        self.signaled = False

    def isSet(self):
        return self.signaled

    def __repr__(self):
        return '<%s; set=%s>' % (object.__repr__(self)[1:-1], self.isSet())


class MenuItem(object):
    def __init__(self, title, **kwargs):
        self.title = title
        self.hidden = False
        self.__dict__.update(kwargs)

    def fw_item(self):
        try:
            item = tuple(self.submenu.fw_menu())
        except AttributeError:
            try:
                item = self.target
            except AttributeError:
                item = lambda: None
        return (unicode(self.title), item)

    def copy(self):
        # note: the title will be specified automatically
        item = MenuItem(**self.__dict__)
        try:
            item.submenu = item.submenu.copy()
        except AttributeError:
            pass
        return item

    def __repr__(self):
        return '<%s; title=%s>' % (object.__repr__(self)[1:-1], repr(self.title))


class Menu(object):
    def __init__(self, title=u'', items=[]):
        if title:
            self.title = title
        else:
            self.title = u''
        for item in items:
            assert isinstance(item, MenuItem)
        self.items = list(items)

    def fw_menu(self):
        return [x.fw_item() for x in self.items if not x.hidden]

    def append(self, item):
        assert isinstance(item, MenuItem)
        self.items.append(item)

    def insert(self, i, item):
        assert isinstance(item, MenuItem)
        self.items.insert(i, item)

    def remove(self, item):
        assert isinstance(item, MenuItem)
        self.items.remove(item)

    def clear(self):
        self.items = []

    def copy(self):
        return Menu(self.title, [x.copy() for x in self.items])

    def __getitem__(self, i):
        return self.items[i]

    def __setitem__(self, i, item):
        self.items[i] = item

    def __delitem__(self, i):
        del self.items[i]

    def __len__(self):
        return len(self.items)

    def find(self, **kwargs):
        items = []
        for item in self.items:
            for name, val in kwargs.items():
                if not hasattr(item, name) or getattr(item, name) != val:
                    break
            else:
                items.append(item)
        return tuple(items)

    def index(self, item):
        return self.items.index(item)

    def __repr__(self):
        return '<%s; items=%s>' % (object.__repr__(self)[1:-1], len(self))

    def __defcompare(a, b):
        return -(unicode(a.title).lower() < unicode(b.title).lower())

    def sort(self, compare=__defcompare):
        self.items.sort(compare)

    def popup(self, full_screen=False, search_field=False):
        if search_field:
            full_screen = True
        if full_screen:
            win = screen.focused_window()
            if win:
                wintitle = win.title
        menu = self
        try:
            while True:
                items = [x for x in menu.items if not x.hidden]
                titles = [unicode(x.title) for x in items]
                if full_screen:
                    if win:
                        win.title = menu.title
                    i = selection_list(titles, search_field)
                elif menu:
                    i = popup_menu(titles, unicode(menu.title))
                else:
                    i = None
                if i is None or i < 0:
                    item = None
                    break
                item = items[i]
                try:
                    menu = item.submenu
                except AttributeError:
                    break
        finally:
            if full_screen and win:
                win.title = wintitle
        return item

    def multichoice(self, style='checkbox', search_field=False):
        items = [x for x in self.items if not x.hidden]
        titles = [unicode(x.title) for x in items]
        win = screen.focused_window()
        if win:
            wintitle = win.title
            win.title = self.title
        try:
            ret = multi_selection_list(titles, style, search_field)
            return tuple([items[x] for x in ret])
        finally:
            if win:
                win.title = wintitle


# size
sizNormal = 'normal'
sizLarge = 'large'
sizFull = 'full'


# orientation
oriAutomatic = 'automatic'
oriPortrait = 'portrait'
oriLandscape = 'landscape'


# Screen._update_fw() mask
_umOrientation = 0x01
_umSize = 0x02
_umBody = 0x04
_umTitle = 0x08
_umMenu = 0x10
_umExit = 0x20
_umAll = 0x3f


class Screen(object):
    def __init__(self):
        self.windows = []

        self.__control_key_timer = None
        self.__control_key_last = None

        self.__blank_win = None
        self.rootwin = None

    def create_window(self, klass=None, *args, **kwargs):
        if klass is None:
            klass = Window
        win = klass(self, *args, **kwargs)
        ofwin = self.focused_window()
        self.windows.append(win)
        if isinstance(win, RootWindow):
            assert self.rootwin is None, 'root window already created'
            self.rootwin = win
        nfwin = self.focused_window()
        if ofwin and ofwin != nfwin:
            ofwin.focus_changed(False)
        if nfwin == win:
            nfwin.focus_changed(True)
            reset_inactivity()
        self.__update_fw()
        return win

    def find_windows(self, *classes):
        if not classes:
            classes = (Window,)
        windows = []
        for win in self.windows:
            for klass in classes:
                if isinstance(win, klass):
                    windows.append(win)
                    break
        return windows

    def close_windows(self, *classes):
        for win in [x for x in self.find_windows(*classes) if x != self.rootwin]:
            if not win.close():
                return False
        return not [x for x in self.find_windows(*classes) if x != self.rootwin]

    def focused_window(self):
        if self.windows:
            win = self.windows[0]
            while win._Window__overlapped:
                win = win._Window__overlapped
            return win

    def redraw(self):
        self.__update_fw()
        e32.ao_yield()

    def create_blank_window(self, title=None):
        if title is None:
            title = _('Please wait...')
        if self.__blank_win and self.__blank_win.is_alive():
            self.__blank_win.title = title
        else:
            self.__blank_win = self.create_window(BlankWindow, title=title)
        self.__blank_win.focus = True
        return self.__blank_win

    def __get_focus(self, win):
        # called internally by Window.focus
        return win == self.focused_window()

    def __set_focus(self, win, focus):
        # called internally by Window.focus
        fwin = self.focused_window()
        if focus:
            # for overlapped windows, get the farthest one
            while True:
                owners = [x for x in self.windows if x.overlapped == win]
                if not owners:
                    break
                win = owners[0]
            # now walk through all overlapped windows and put them at the top
            while True:
                self.windows.remove(win)
                self.windows.insert(0, win)
                if not win._Window__overlapped:
                    break
                win = win._Window__overlapped
        else: # focus = False
            # walk through all overlapped windows and put them at the bottom
            while True:
                self.windows.remove(win)
                self.windows.append(win)
                if not win._Window__overlapped:
                    break
                win = win._Window__overlapped
        win = self.focused_window()
        if fwin != win:
            fwin.focus_changed(False)
            win.focus_changed(True)
            reset_inactivity()
            # update screen so the topmost window is visible
            self.__control_key_reset(fwin)
            self.__update_fw()

    def __close(self, win):
        # called internally by Window.close()
        fwin = self.focused_window()
        self.windows.remove(win)
        for w in [w for w in self.windows if w._Window__overlapped == win]:
            w._Window__overlapped = None
        if win == self.rootwin:
            self.rootwin = None
        if fwin == win:
            win.focus_changed(False)
        fwin = self.focused_window()
        if fwin:
            fwin.focus_changed(True)
        self.__control_key_reset(win)
        self.__update_fw()

    def __update_fw(self, mask=_umAll):
        win = self.focused_window()
        if win:
            if mask & _umOrientation:
                app.orientation = win.orientation
            if mask & _umSize:
                app.screen = win.size
            if mask & _umBody:
                app.body = win.body
            if mask & _umTitle:
                app.title = unicode(win.title)
            if mask & _umMenu:
                app.menu = win.menu.fw_menu()
            if mask & _umExit:
                app.exit_key_handler = win.close

    def __ekeyyes_handler(self):
        win = self.focused_window()
        in_time = (self.__control_key_timer is not None)
        if in_time:
            self.__control_key_timer.cancel()
        self.__control_key_timer = e32.Ao_timer()
        self.__control_key_timer.after(1.5, lambda: self.__control_key_reset(win))
        if win is not None and hasattr(win._Window__body, 'focus'):
            win._Window__body.focus = False
        if in_time and self.__control_key_last is None:
            self.__control_key_reset(win)
            schedule(self.__window_selector)
            return
        if win is not None:
            def make_key_handler(key):
                return lambda: self.__control_key_handler(key)
            for key in win._Window__control_keys:
                win._Window__body.bind(key, make_key_handler(key))
        self.__control_key_last = None

    def __control_key_reset(self, win):
        # finishes control key processing
        if self.__control_key_timer is not None:
            self.__control_key_timer.cancel()
            self.__control_key_timer = None
            if win is not None:
                if hasattr(win._Window__body, 'focus'):
                    win._Window__body.focus = True
                for key in win._Window__control_keys:
                    # FIXME: should be set to None instead of lambda: None,
                    # but it crashes when done so
                    win._Window__body.bind(key, lambda: None)
                # restore normal bindings
                win._Window__set_keys(win._Window__keys)
        self.__control_key_last = None

    def __control_key_handler(self, key):
        win = self.focused_window()
        if self.__control_key_timer is None:
            return
        self.__control_key_timer.cancel()
        if self.__control_key_last not in [None, key]:
            self.__control_key_reset(win)
            # if this key should be catched not as a control key,
            # notify the window about it
            if key in win._Window__keys:
                win.key_press(key)
            return
        self.__control_key_timer = e32.Ao_timer()
        self.__control_key_timer.after(1.0, lambda: self.__control_key_reset(win))
        if win.control_key_press(key):
            # hack to suppress the key press
            app.body = Canvas()
            schedule(lambda: self.__update_fw(_umBody))
        self.__control_key_last = key

    def __window_selector(self):
        win = self.focused_window()
        # if the focused window shouldn't appear in the selector, try to
        # use one of its owners instead to get the title; if none of them
        # should appear, use a selector without title
        while not win.selector:
            owners = [x for x in self.windows if x.overlapped == win]
            if not owners:
                title = None
                break
            win = owners[0]
        else:
            title = win._Window__title
        menu = Menu(title)
        for win in [x for x in self.windows if x != win and x.selector]:
            menu.append(MenuItem(win._Window__title, window=win))
        item = menu.popup()
        if item:
            item.window.focus = True

    def get_windows_menu(self):
        menu = Menu()
        def make_activator(win):
            def activate():
                win.focus = True
            return activate
        for win in self.windows:
            if win.selector:
                menu.append(MenuItem(win._Window__title, window=win, target=make_activator(win)))
        return menu

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, i):
        return self.windows[i]


class Window(object):
    def __init__(self, screen, title=None, size=None, orientation=None, selector=True, **kwargs):
        self.__screen = screen
        if title is None:
            title = self.__class__.__name__
        self.__title = title
        self.__body = None
        self.__menu = Menu()
        if size is None:
            try:
                size = self.__screen.rootwin.size
            except AttributeError:
                size = sizNormal
        self.__size = size
        if orientation is None:
            try:
                orientation = self.__screen.rootwin.orientation
            except AttributeError:
                orientation = oriAutomatic
        self.__orientation = orientation
        self.selector = selector
        self.__overlapped = None
        self.__keys = []
        self.__control_keys = []
        self.__modal_event = None
        self.modal_result = None

    def is_alive(self):
        return bool(self.__screen is not None)

    def can_close(self):
        return not self.__overlapped or not self.__overlapped.is_alive()

    def close(self):
        if self.is_alive() and self.can_close():
            # we want is_alive() to return False when we call screen._Screen__close()
            # so we clear self.__screen first
            screen = self.__screen
            self.__screen = None
            screen._Screen__close(self)
            if self.__body is not None:
                for key in self.__keys:
                    self.__body.bind(key, None)
            if self.__modal_event:
                self.__modal_event.set()
                # this delay is here to allow the active object that called modal()
                # to finish; if we're here because the application closes and all
                # windows are being closed, not letting the AO finish itself would
                # lead to a crash ("app closed" error)
                e32.ao_sleep(0.1)
            return True
        return False

    def modal(self, owner=None):
        if self.is_alive():
            assert self.__modal_event is None, 'modal() already in progress'
            self.__modal_event = Event()
            self.focus = True
            if owner:
                state = owner.overlapped, self.selector
                owner.overlapped = self
                self.selector = False
            self.__modal_event.wait()
            if owner:
                owner.overlapped, self.selector = state
            self.__modal_event = None
            return self.modal_result

    def key_press(self, key):
        return False

    def control_key_press(self, key):
        return False

    def focus_changed(self, focus):
        pass

    def reset_control_key(self):
        if self.focus:
            self.__screen._Screen__control_key_reset(self)

    def __set_title(self, title):
        self.__title = title
        self.__update_fw(_umTitle)

    def __set_body(self, body):
        self.__body = body
        self.__update_fw(_umBody)
        if self.is_alive() and hasattr(body, 'bind'):
            body.bind(EKeyYes, self.__screen._Screen__ekeyyes_handler)
            def make_key_handler(key):
                return lambda: self.key_press(key)
            for key in self.__keys:
                body.bind(key, make_key_handler(key))

    def __set_menu(self, menu):
        self.__menu = menu
        self.__update_fw(_umMenu)

    def update_menu(self):
        self.__update_fw(_umMenu)

    def __set_size(self, size):
        self.__size = size
        self.__update_fw(_umSize)

    def __set_orientation(self, orientation):
        self.__orientation = orientation
        self.__update_fw(_umOrientation)

    def __set_keys(self, keys):
        keys = list(keys)
        try:
            keys.remove(EKeyYes)
        except ValueError:
            pass
        if self.__body is not None:
            for key in self.__keys:
                self.__body.bind(key, lambda: None)
        self.__keys = keys
        if self.__body is not None:
            def make_key_handler(key):
                return lambda: self.key_press(key)
            for key in keys:
                self.__body.bind(key, make_key_handler(key))

    def __set_control_keys(self, control_keys):
        keys = list(control_keys)
        try:
            keys.remove(EKeyYes)
        except ValueError:
            pass
        self.__control_keys = keys

    def __update_fw(self, mask=_umAll):
        if self.focus:
            self.__screen._Screen__update_fw(mask)

    def __get_focus(self):
        if self.is_alive():
            return self.__screen._Screen__get_focus(self)
        return False

    def __set_focus(self, focus):
        if self.is_alive():
            self.__screen._Screen__set_focus(self, focus)

    def __set_overlapped(self, win):
        self.__overlapped = win
        self.__update_fw()

    def __repr__(self):
        return '<%s; title=%s>' % (object.__repr__(self)[1:-1], repr(self.title))

    title = property(lambda self: self.__title, __set_title)
    body = property(lambda self: self.__body, __set_body)
    menu = property(lambda self: self.__menu, __set_menu)
    size = property(lambda self: self.__size, __set_size)
    orientation = property(lambda self: self.__orientation, __set_orientation)
    focus = property(__get_focus, __set_focus)
    keys = property(lambda self: self.__keys, __set_keys)
    control_keys = property(lambda self: self.__control_keys, __set_control_keys)
    overlapped = property(lambda self: self.__overlapped, __set_overlapped)


class RootWindow(Window):
    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = app.title
        if 'selector' not in kwargs:
            kwargs['selector'] = False
        Window.__init__(self, *args, **kwargs)
        self.body = Canvas(redraw_callback=self.redraw_callback,
                           event_callback=self.event_callback)

    def redraw_callback(self, rect):
        self.body.clear(0x888888)

    def event_callback(self, event):
        # can be overridden
        pass

    def close(self):
        if self.is_alive():
            # close all windows except root window
            if not self._Window__screen.close_windows():
                return False
            # close root window (self)
            return Window.close(self)
        return False
    

class BlankWindow(Window):
    def __init__(self, *args, **kwargs):
        if 'selector' not in kwargs:
            kwargs['selector'] = False
        Window.__init__(self, *args, **kwargs)
        self.body = Canvas(redraw_callback=self.redraw_callback)

    def redraw_callback(self, rect):
        self.body.clear(0xcccccc)

    def focus_changed(self, focus):
        Window.focus_changed(self, focus)
        if not focus:
            self.close()


class Tab(object):
    def __init__(self, title=None, body=None, menu=None, keys=None, control_keys=None):
        if title is None:
            title = self.__class__.__name__
        if menu is None:
            menu = Menu()
        if keys is None:
            keys = []
        if control_keys is None:
            control_keys = []
        self.__title = title
        self.__body = body
        self.__menu = menu
        self.__keys = keys
        self.__control_keys = control_keys
        self.window = None

    def __set_window_property(self, prop, value):
        if self.window is not None:
            if self.window.get_active_tab() == self:
                setattr(self.window, prop, value)

    def __set_title(self, title):
        self.__title = title
        self.__set_window_property('title', self.__title)

    def __set_body(self, body):
        self.__body = body
        self.__set_window_property('body', body)

    def __set_menu(self, menu):
        self.__menu = menu
        self.__set_window_property('menu', menu)

    def __set_keys(self, keys):
        self.__keys = keys
        self.__set_window_property('keys', keys)

    def __set_control_keys(self, control_keys):
        self.__control_keys = control_keys
        self.__set_window_property('control_keys', control_keys)

    title = property(lambda self: self.__title, __set_title)
    body = property(lambda self: self.__body, __set_body)
    menu = property(lambda self: self.__menu, __set_menu)
    keys = property(lambda self: self.__keys, __set_keys)
    control_keys = property(lambda self: self.__control_keys, __set_control_keys)


class TabbedWindow(Window):
    def __init__(self, *args, **kwargs):
        Window.__init__(self, *args, **kwargs)
        self.__tabs = ()
        self.__active_tab = -1

    def focus_changed(self, focus):
        Window.focus_changed(self, focus)
        if focus and self.tabs:
            app.set_tabs([unicode(x.title) for x in self.tabs], self.__tab_changed)
            app.activate_tab(self.__active_tab)
        else:
            app.set_tabs([], None)

    def tab_changed(self):
        pass

    def __update_win(self):
        if self.__active_tab >= 0:
            tab = self.__tabs[self.__active_tab]
            self._Window__keys = tab.keys
            self._Window__control_keys = tab.control_keys
            self._Window__body = None
            self.body = tab.body
            self.menu = tab.menu
        else:
            self.keys = ()
            self.control_keys = ()
            self.body = None
            self.menu = Menu()

    def __tab_changed(self, n):
        self.__active_tab = n
        self.__update_win()
        e32.ao_yield()
        self.tab_changed()

    def __set_tabs(self, tabs):
        self.__tabs = tuple(tabs)
        if len(tabs) <= self.__active_tab:
            self.__active_tab = len(tabs) - 1
        elif self.__active_tab < 0:
            self.__active_tab = 0
        for tab in tabs:
            tab.window = self
        if self.focus:
            if tabs:
                app.set_tabs([unicode(x.title) for x in tabs], self.__tab_changed)
            else:
                app.set_tabs([], None)
        self.__update_win()
        self.tab_changed()

    def __set_active_tab(self, n):
        if n >= len(self.tabs):
            n = len(self.tabs) - 1
        elif n < 0:
            n = 0
        self.__tab_changed(n)
        if self.focus:
            app.activate_tab(n)

    def get_active_tab(self):
        return self.__tabs[self.__active_tab]

    tabs = property(lambda self: self.__tabs, __set_tabs)
    active_tab = property(lambda self: self.__active_tab, __set_active_tab)


fbmOpen, \
fbmSave = range(2)

class FileBrowserWindow(Window):
    links = []
    icons_path = ''
    settings_path = ''
    max_recents = 7

    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = _('File browser')
        Window.__init__(self, *args, **kwargs)
        self.mode = kwargs.get('mode', fbmOpen)
        self.path, self.name = os.path.split(kwargs.get('path', ''))
        # gtitle is the global title, 'File browser' or set by user
        # ctitle is the current title, together with filter they make the window title
        self.gtitle = self.ctitle = self.title
        if not os.path.exists(self.icons_path):
            raise IOError('Missing file browser icons file')
        icons_type = os.path.splitext(self.icons_path)[-1].lower()
        icons_list = [('loading', 8, 16390),
                      ('info', 6, 16390),
                      ('drive', 2, 16384),
                      ('folder', 0, 16388),
                      ('empty', 12, 16386),
                      ('.txt', 4, 16394),
                      ('.py', 10, 16392)]
        self.icons = {}
        path = self.icons_path.decode('utf8')
        for name, mbm, mif in icons_list:
            if icons_type == '.mif':
                self.icons[name] = Icon(path, mif, mif+1)
            else:
                self.icons[name] = Icon(path, mbm, mbm+1)
        self.settings = Settings(self.settings_path)
        self.settings.add('main', SettingsGroup())
        self.settings.main.add('recents', Setting('Recents', []))
        self.settings.load_if_available()
        self.body = Listbox([(_('(empty)'), self.icons['info'])], self.select_click)
        self.keys += (EKeyLeftArrow, EKeyRightArrow, EKeyStar, EKey0, EKeyHash, EKeyBackspace)
        self.control_keys += (EKeyUpArrow, EKeyDownArrow)
        self.busy = False
        self.DRIVE, self.DIR, self.FILE, self.INFO = range(4)
        self.filterstr = u''
        self.update(self.name)

    def close(self):
        r = Window.close(self)
        if r:
            self.menu = Menu()
        return r

    def add_link(cls, link, title=None):
        if link and link[1:] != ':\\' and os.path.exists(link):
            if link.lower() in [x[0].lower() for x in cls.links]:
                return False
            if title is None:
                path, name = os.path.split(link)
                title = _('%s in %s') % (name.decode('utf8'), path.decode('utf8'))
            cls.links.append((link, title))
            return True
        return False
    add_link = classmethod(add_link)

    def add_recent(self, filename):
        recents = self.settings.main.recents
        for name in recents:
            if name.lower() == filename.lower():
                recents.remove(name)
                break
        else:
            if len(recents) == self.max_recents:
                recents.pop()
        recents.insert(0, filename)
        self.settings.save()

    def get_file_icon(self, name):
        ext = os.path.splitext(name)[1].lower()
        try:
            return self.icons[ext]
        except KeyError:
            return self.icons['empty']

    def update(self, mark=''):
        self.body.set_list([(_('Loading...'), self.icons['loading'])])
        if self.path == '':
            self.ctitle = self.gtitle
            e32.ao_yield()
            # drives
            self.lstall = [(self.DRIVE, self.icons['drive'], x, x.encode('utf8')) for x in e32.drive_list()]
            # links
            def format(link):
                if os.path.isfile(link[0]):
                    return (self.FILE, self.get_file_icon(link[0]), link[1], link[0])
                else:
                    return (self.DIR, self.icons['folder'], link[1], link[0])
            self.lstall += map(format, self.links)
        elif self.path == 'recents':
            self.ctitle = _('Recent files')
            def format(filename):
                path, name = os.path.split(filename)
                title = _('%s in %s') % (name.decode('utf8'), path.decode('utf8'))
                return (self.FILE, self.get_file_icon(filename), title, filename)
            recents = self.settings.main.recents
            recentslen = len(recents)
            # remove deleted recents
            for filename in list(recents):
                if not os.path.exists(filename):
                    recents.remove(filename)
            if len(recents) != recentslen:
                self.settings.save()
            self.lstall = map(format, recents)
        else:
            if self.path[-2:] == ':\\':
                # we are in drive's root directory
                self.ctitle = self.path[:2].decode('utf8')
            else:
                self.ctitle = os.path.split(self.path)[1].decode('utf8')
            e32.ao_yield()
            def format(name):
                if os.path.isfile(os.path.join(self.path, name)):
                    return (self.FILE, self.get_file_icon(name), name.decode('utf8'), name)
                else:
                    return (self.DIR, self.icons['folder'], name.decode('utf8'), name)
            try:
                ldir = os.listdir(self.path)
            except OSError:
                note(_('Cannot list directory'), 'error')
                self.parent_click()
                return
            else:
                self.lstall = map(format, ldir)
        def compare(a, b):
            if a[0] > b[0]:
                return 0
            if a[0] < b[0]:
                return -1
            return -(unicode(a[2]).lower() < unicode(b[2]).lower())
        self.lstall.sort(compare)
        if self.path == '':
            # add link to recent files at the top
            self.lstall.insert(0, (self.DIR, self.icons['folder'], _('Recent files'), 'recents'))
        active = 0
        if mark != '':
            try:
                active = [x[3].lower() for x in self.lstall].index(mark.lower())
            except ValueError:
                pass
        if not self.lstall:
            self.lstall.append((self.INFO, self.icons['info'], _('(empty)'), None))
        self.set_list(active, dofilter=True)
        self.make_menu()

    def make_menu(self):
        menu = Menu()
        menu.append(MenuItem(_('Open'), target=self.select_click))
        if self.path == 'recents':
            menu.append(MenuItem(_('Drives'), target=self.drives_click))
            menu.append(MenuItem(_('Delete'), target=self.delete_click))
        elif self.path != '':
            if self.mode == fbmSave:
                menu.append(MenuItem(_('Save here...'), target=self.save_click))
            menu.append(MenuItem(_('Parent'), target=self.parent_click))
            menu.append(MenuItem(_('Drives'), target=self.drives_click))
            menu.append(MenuItem(_('Rename'), target=self.rename_click))
            menu.append(MenuItem(_('Delete'), target=self.delete_click))
            menu.append(MenuItem(_('Create folder...'), target=self.mkdir_click))
        if self.filterstr:
            fmenu = efmenu = Menu()
            fmenu.append(MenuItem(_('Show all'), target=self.showall_click))
            menu.append(MenuItem(_('Filter'), submenu=fmenu))
        else:
            fmenu = None
            efmenu = menu
        efmenu.append(MenuItem(_('Edit filter...'), target=self.editfilter_click))
        menu.append(MenuItem(_('Exit'), target=self.close))
        self.menu = menu
        self.filtermenu = fmenu

    def set_list(self, active=None, dofilter=False):
        if active is None:
            active = self.body.current()
        if dofilter:
            if self.filterstr:
                self.lst = [x for x in self.lstall if x[0] == self.INFO or unicode(x[2]).lower().find(self.filterstr) >= 0]
                if not self.lst:
                    self.lst.append((self.INFO, self.icons['info'], _('(no match)'), None))
                try:
                    active = self.lst.index(self.lstall[active])
                except ValueError:
                    active = 0
                self.title = '%s | %s' % (self.filterstr, self.ctitle)
            else:
                self.lst = self.lstall
                self.title = self.ctitle
        if active < 0:
            active = 0
        elif active >= len(self.lst):
            active = len(self.lst) - 1
        self.body.set_list([(unicode(x[2]), x[1]) for x in self.lst], active)

    def select_click(self):
        if self.busy:
            return
        self.busy = True
        item = self.lst[self.body.current()]
        if item[0] == self.DRIVE:
            self.path = '%s\\' % item[3]
            self.filterstr = u''
            self.update()
        elif item[0] == self.DIR:
            self.path = os.path.join(self.path, item[3])
            self.filterstr = u''
            self.update()
        elif item[0] == self.FILE:
            if self.mode == fbmOpen:
                if self.path == 'recents':
                    self.path = ''
                self.path = os.path.join(self.path, item[3])
                self.modal_result = self.path
                self.add_recent(self.path)
                self.close()
            else:
                self.save_click(os.path.splitext(item[3])[0] + os.path.splitext(self.name)[1])
        self.busy = False

    def key_press(self, key):
        if key == EKeyLeftArrow:
            self.parent_click()
        elif key == EKeyRightArrow:
            self.enter_click()
        elif key == EKeyBackspace:
            self.delete_click()
        elif key == EKeyStar:
            self.filter_click()
        elif key == EKey0:
            self.info_click()
        elif key == EKeyHash:
            self.drives_click()
        else:
            return Window.key_press(self, key)

    def control_key_press(self, key):
        if key == EKeyUpArrow:
            self.set_list(self.body.current() - 5)
        elif key == EKeyDownArrow:
            self.set_list(self.body.current() + 5)
        else:
            return Window.control_key_press(self, key)
        # return False to prevent flashing
        return False

    def filter_click(self):
        if self.filtermenu is not None:
            item = self.filtermenu.popup()
            if item:
                item.target()
        else:
            self.editfilter_click()

    def showall_click(self):
        self.filterstr = u''
        self.set_list(dofilter=True)
        self.make_menu()

    def editfilter_click(self):
        f = query(_('Filter:'), 'text', self.filterstr)
        if f:
            self.filterstr = f.lower()
            self.set_list(dofilter=True)
            self.make_menu()

    def enter_click(self):
        item = self.lst[self.body.current()]
        if item[0] == self.FILE:
            path, name = os.path.split(item[3])
            if path:
                self.path = path
                self.update(name)
        else:
            self.select_click()

    def parent_click(self):
        if self.path != '':
            if self.path[-2:] == ':\\':
                mark = self.path[:2]
                self.path = ''
            else:
                self.path, mark = os.path.split(self.path)
            self.filterstr = u''
            self.update(mark)

    def drives_click(self):
        if self.path != '':
            mark = self.path[:2]
            self.path = ''
            self.filterstr = u''
            self.update(mark)

    def save_click(self, name=None):
        if name is None:
            name = self.name
        name, ext = os.path.splitext(name)
        path = None
        while True:
            name = query(_('Name (%s):') % ext.decode('utf8'), 'text', name.decode('utf8'))
            if name is None:
                return
            name = name.encode('utf8')
            name, newext = os.path.splitext(name)
            if newext:
                ext = newext
            path = os.path.join(self.path, name + ext)
            if os.path.exists(path):
                if os.path.isdir(path):
                    note(_('Invalid name'), 'error')
                    continue
                elif not query(_('Already exists!\nOverwrite?'), 'query'):
                    continue
            break
        self.add_recent(path)
        self.name = name + ext
        self.modal_result = path
        self.close()

    def delete_click(self):
        item = self.lst[self.body.current()]
        if item[0] not in [self.FILE, self.DIR]:
            return
        if query(_('Delete %s?') % item[2], 'query'):
            try:
                path = os.path.join(self.path, item[3])
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    os.rmdir(path)
                self.update()
            except OSError:
                note(_('Cannot delete'), 'error')

    def rename_click(self):
        item = self.lst[self.body.current()]
        if item[0] not in [self.FILE, self.DIR]:
            return
        name, ext = os.path.splitext(item[3])
        while True:
            name = query(_('Name (%s):') % ext.decode('utf8'), 'text', name.decode('utf8'))
            if name is None:
                break
            name = name.encode('utf8')
            name, newext = os.path.splitext(name)
            if newext:
                ext = newext
            src = os.path.join(self.path, item[3])
            dst = os.path.join(self.path, name + ext)
            try:
                if os.path.exists(dst) and src.lower() != dst.lower():
                    if os.path.isdir(dst):
                        note(_('Already exists as a directory!'), 'error')
                        continue
                    if not query(_('Already exists!\nOverwrite?'), 'query'):
                        continue
                    os.remove(dst)
                os.rename(src, dst)
                self.update(name + ext)
                break
            except OSError:
                note(_('Cannot rename'), 'error')
                break

    def mkdir_click(self):
        name = query(_('Name:'), 'text')
        if name is not None:
            try:
                os.mkdir(os.path.join(self.path, name.encode('utf8')))
                self.update(name.encode('utf8'))
            except OSError:
                note(_('Cannot create folder'), 'error')

    def info_click(self):
        item = self.lst[self.body.current()]
        if item[0] not in [self.FILE, self.DIR]:
            return
        import time
        stat = os.stat(os.path.join(self.path, item[3]))
        if item[0] == self.FILE:
            n = stat.st_size
            text = '%d bytes' % n
            if n > 1024:
                n /= 1024.0
                text = '%.1f KB' % n
            if n > 1024:
                n /= 1024.0
                text = '%.1f MB' % n
            text += '\n'
        else:
            text = ''
        text += time.strftime('%d.%m.%Y %H:%M:%S', time.localtime(stat.st_mtime))
        try:
            self.popup = InfoPopup()
            self.popup.show(unicode(text))
        except NameError:
            note(unicode(text))


class Setting(object):
    def __init__(self, title, value):
        self.title = title
        self.value = value
        self.original = value

    def changed(self):
        return self.original != self.value

    def store(self):
        self.original = self.value

    def restore(self):
        self.value = self.original

    def get(self):
        return self.value

    def set(self, value):
        self.value = self.original = value

    def edit(self):
        return False

    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)


class TextSetting(Setting):
    def __init__(self, title, value=u''):
        Setting.__init__(self, title, value)

    def edit(self):
        v = query(unicode(self.title), 'text', unicode(self.value))
        if v is not None:
            self.value = v
            return True
        return False


class NumberSetting(Setting):
    def __init__(self, title, value=0, vmin=None, vmax=None):
        if vmin is not None and vmax is not None and vmin > vmax:
            vmin = vmax
        if vmin is not None and value < vmin:
            value = vmin
        if vmax is not None and value > vmax:
            value = vmax
        Setting.__init__(self, title, value)
        self.vmin = vmin
        self.vmax = vmax

    def edit(self):
        v = self.value
        while True:
            v = query(unicode(self.title), 'number', v)
            if v is None:
                return False
            if self.vmin is not None and v < self.vmin:
                note(_('Minimal value is %s') % self.vmin)
                continue
            if self.vmax is not None and v > self.vmax:
                note(_('Maximal value is %s') % self.vmax)
                continue
            self.value = v
            break
        return True


class FloatSetting(NumberSetting):
    def __init__(self, title, value=0.0, vmin=None, vmax=None):
        NumberSetting.__init__(self, title, float(value), float(vmin), float(vmax))

    def edit(self):
        v = self.value
        while True:
            v = query(unicode(self.title), 'float', v)
            if v is None:
                return False
            if self.vmin is not None and v < self.vmin:
                # we use %s to share a translatable string with NumberSetting
                note(_('Minimal value is %s') % ('%.2f' % self.vmin))
                continue
            if self.vmax is not None and v > self.vmax:
                # we use %s to share a translatable string with NumberSetting
                note(_('Maximal value is %s') % ('%.2f' % self.vmax))
                continue
            self.value = v
            break
        return True


class BoolSetting(Setting):
    def __init__(self, title, value=False, true=None, false=None):
        if true is None:
            true = _('On')
        if false is None:
            false = _('Off')
        Setting.__init__(self, title, value)
        self.true = true
        self.false = false

    def edit(self):
        self.value = not self.value
        return True

    def __unicode__(self):
        if self.value:
            return unicode(self.true)
        return unicode(self.false)


class ComboSetting(Setting):
    def __init__(self, title, value=None, choices=[]):
        Setting.__init__(self, title, value)
        self.choices = list(choices)

    def edit(self):
        lst = map(unicode, self.choices)
        try:
            c = self.choices.index(self.value)
            s = u'* %s' % lst[c]
            del lst[c]
            lst.insert(0, s)
        except ValueError:
            c = 0
        i = popup_menu(lst, unicode(self.title))
        if i is not None:
            if i == 0:
                i = c
            elif i <= c:
                i -= 1
            self.value = self.choices[i]
            return True
        return False


class ValueComboSetting(ComboSetting):
    def __init__(self, title, value=None, choices=[]):
        ComboSetting.__init__(self, title, value, [val for name, val in choices])
        self.valuechoices = list(choices)

    def edit(self):
        choices = self.choices
        value = self.value
        try:
            self.choices = [name for name, val in self.valuechoices]
            self.value = dict([(val, name) for name, val in self.valuechoices])[self.value]
            ret = ComboSetting.edit(self)
            if ret:
                self.value = dict(self.valuechoices)[self.value]
            else:
                self.value = value
            return ret
        finally:
            self.choices = choices

    def __str__(self):
        return str(dict([(val, name) for name, val in self.valuechoices])[self.value])

    def __unicode__(self):
        return unicode(dict([(val, name) for name, val in self.valuechoices])[self.value])


class TimeSetting(Setting):
    def __init__(self, title, value=0.0):
        Setting.__init__(self, title, value)

    def edit(self):
        v = query(unicode(self.title), 'time', self.value)
        if v is not None:
            self.value = v
            return True
        return False

    def __str__(self):
        from time import strftime, localtime
        return strftime('%H:%M', localtime(self.value))

    def __unicode__(self):
        from time import strftime, localtime
        return unicode(strftime('%H:%M', localtime(self.value)))


class DateSetting(Setting):
    def __init__(self, title, value=0.0):
        Setting.__init__(self, title, value)

    def edit(self):
        v = query(unicode(self.title), 'date', self.value)
        if v is not None:
            # the value returned by date query seems to always
            # be shifted by timezone; to complicate things more,
            # on newer platforms it is shifted by 3600 seconds
            # more :\
            from time import timezone
            # NOTE: i'm not sure if the inreased shift started
            # with version 3.0 !
            if e32.s60_version_info >= (3, 0):
                timezone -= 3600
            self.value = v - timezone
            return True
        return False

    def __str__(self):
        from time import strftime, localtime
        return strftime('%d.%m.%Y', localtime(self.value))

    def __unicode__(self):
        from time import strftime, localtime
        return unicode(strftime('%d.%m.%Y', localtime(self.value)))


class ShortkeySettingWindow(Window):
    def __init__(self, *args, **kwargs):
        Window.__init__(self, *args, **kwargs)
        self.body = Text()
        if 'text' not in kwargs:
            kwargs['text'] = u'%s\n' % _('Press a new shortkey or select Exit to cancel this dialog.')
        self.body.add(unicode(kwargs['text']))
        self.menu.append(MenuItem(_('Exit'), target=self.close))
        self.control_keys = (EKey0, EKey1, EKey2, EKey3, EKey4, EKey5, EKey6, EKey7, EKey8,
            EKey9, EKey0, EKeyStar, EKeyHash)

    def control_key_press(self, key):
        self.modal_result = key
        self.close()


class ShortkeySetting(Setting):
    def __init__(self, title, value=EKey1):
        Setting.__init__(self, title, value)

    def edit(self):
        key = screen.create_window(ShortkeySettingWindow, title=self.title).modal()
        if key is not None:
            self.value = key
            return True
        return False

    def __str__(self):
        return str(self.__unicode__())

    def __unicode__(self):
        return _('Green + %s') % unichr(self.value)


class CustomSetting(Setting):
    def __init__(self, title, value=None, edit_callback=None):
        Setting.__init__(self, title, value)
        self.edit_callback = edit_callback

    def edit(self):
        if self.edit_callback:
            v = self.edit_callback(self.title, self.value)
            if v is not None:
                self.value = v


class SettingsGroup(object):
    def __init__(self, title=''):
        self.title = title
        self.objs = {}
        self.order = []

    def add(self, name, obj):
        if isinstance(obj, Setting):
            self.objs[name] = obj
            self.order.append(name)
        else:
            raise TypeError('\'obj\' must be a Setting object')

    def clear(self):
        self.objs.clear()
        self.order = []

    def all(self):
        return [(x, self.objs[x]) for x in self.order]

    def get(self):
        return self
        
    def set(self, value):
        raise AttributeError('Cannot set a SettingsGroup (to %s)' % repr(value))

    def __getitem__(self, name):
        return self.objs[name]

    def __getattr__(self, name):
        if name == 'objs':
            raise AttributeError
        try:
            obj = self.objs[name]
        except KeyError:
            raise AttributeError('%s object has no attribute %s' % (repr(self), repr(name)))
        else:
            return obj.get()

    def __setattr__(self, name, value):
        try:
            obj = self.objs[name]
        except (AttributeError, KeyError):
            return object.__setattr__(self, name, value)
        else:
            obj.set(value)

    def __contains__(self, name):
        return name in self.objs


class Settings(SettingsGroup):
    def __init__(self, filename, title=None):
        if title is None:
            title = _('Settings')
        SettingsGroup.__init__(self, title)
        self.filename = filename
        self.window = None

    def set_filename(self, filename):
        self.filename = filename

    def load(self):
        import marshal
        f = file(self.filename, 'rb')
        while True:
            try:
                # all versions of the file had name-value pairs
                name = marshal.load(f)
                value = marshal.load(f)
                try:
                    gname, name = name.split('/')
                except ValueError:
                    # old file version
                    continue
                try:
                    self[gname][name].set(value)
                except KeyError:
                    # old settings / old file version
                    pass
            except EOFError:
                break
        f.close()

    def save(self):
        import marshal
        f = file(self.filename, 'wb')
        for gname, group in self.all():
            for name, item in group.all():
                marshal.dump('%s/%s' % (gname, name), f)
                marshal.dump(item.get(), f)
        f.close()

    def load_if_available(self):
        try:
            self.load()
        except IOError:
            pass

    def edit(self):
        if self.window:
            self.window.focus = True
            return False
        self.window = screen.create_window(SettingsWindow,
                    settings=self,
                    title=self.title)
        r = self.window.modal()
        self.window = None
        return r

    def add(self, name, obj):
        if isinstance(obj, SettingsGroup):
            self.objs[name] = obj
            self.order.append(name)
        else:
            raise TypeError('\'obj\' must be a SettingsGroup object')

    def get(self):
        raise TypeError('method not implemented')
        
    def set(self, value):
        raise TypeError('method not implemented')


class SettingsWindow(TabbedWindow):
    def __init__(self, *args, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = _('Settings')
        TabbedWindow.__init__(self, *args, **kwargs)
        self.settings = kwargs['settings']
        menu = Menu()
        menu.append(MenuItem(_('Change'), target=self.change_click))
        menu.append(MenuItem(_('Save'), target=self.save_click))
        menu.append(MenuItem(_('Exit'), target=self.close))
        tabs = []
        for gname, group in self.settings.all():
            items = group.all()
            if not items:
                continue
            tab = Tab(group.title)
            tab.group = group
            tab.menu = menu
            tab.body = Listbox([(unicode(item.title), unicode(item)) \
                for name, item in items], self.change_click)
            tabs.append(tab)
        if not tabs:
            raise RuntimeError('No settings to edit')
        self.tabs = tabs
        self.modal_result = False

    def can_close(self):
        if not TabbedWindow.can_close(self):
            return False
        items = []
        for gname, group in self.settings.all():
            for name, item in group.all():
                if item.changed():
                    items.append(item)
        if items:
            if query(_('Save changes?'), 'query'):
                for item in items:
                    item.store()
                self.settings.save()
                self.modal_result = True
            else:
                for item in items:
                    item.restore()
        return True

    def close(self):
        r = TabbedWindow.close(self)
        if r:
            self.menu = Menu()
        return r

    def change_click(self):
        tab = self.get_active_tab()
        if tab.group.all()[tab.body.current()][-1].edit():
            tab.body.set_list([(unicode(item.title), unicode(item)) \
                for name, item in tab.group.all()], tab.body.current())

    def save_click(self):
        for gname, group in self.settings.all():
            for name, item in group.all():
                if item.changed():
                    item.store()
        self.settings.save()
        self.modal_result = True
        note(_('Changes saved'))


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


def available_text_fonts():
    'Returns a sorted list of text fonts.'

    # fonts which names start with one of these followed by a digit will be filtered out
    bad = [u'acalc', u'acb', u'aco', u'acp']
    all = available_fonts()

    fonts = []
    for f in all:
        # additional unusable font from 3rd edition phones
        if f == u'Series 60 ZDigi':
            continue
        for b in bad:
            try:
                if f.lower().startswith(b) and f[len(b)].isdigit():
                    # bad
                    break
            except IndexError:
                pass
        else:
            fonts.append(f)
    def compare(a, b):
        return -(a.lower() < b.lower())
    fonts.sort(compare)

    return fonts


def schedule(target, *args, **kwargs):
    e32.ao_sleep(0, lambda: target(*args, **kwargs))


if e32.s60_version_info < (2, 8):
    (EScreen,
     EApplicationWindow,
     EStatusPane,
     EMainPane,
     EControlPane,
     ESignalPane,
     EContextPane,
     ETitlePane,
     EBatteryPane,
     EUniversalIndicatorPane,
     ENaviPane,
     EFindPane,
     EWallpaperPane,
     EIndicatorPane,
     EAColumn,
     EBColumn,
     ECColumn,
     EDColumn,
     EStaconTop,
     EStaconBottom,
     EStatusPaneBottom,
     EControlPaneBottom,
     EControlPaneTop,
     EStatusPaneTop) = range(24)

    __layout = {
        EApplicationWindow: ((176, 208), (0, 0)),
        EMainPane: ((176, 144), (0, 44)),
        # TODO: Add other ids
    }

    def layout(eid):
        try:
            return __layout[eid]
        except KeyError:
            return ((0, 0), (0, 0))
else:
    def layout(eid):
        return app.layout(eid)


# default screen object
screen = Screen()

# i18n object
translator = _ = Translator()

# global InfoPopup
try:
    infopopup = InfoPopup()
except NameError:
    pass
