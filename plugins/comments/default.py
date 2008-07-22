#
# default.py
#
# Ped plugin adding a configurable shortkey to insert/remove comment char
# from the beginning of a line.
#
# Copyright (c) 2008, Arkadiusz Wahlig
# <arkadiusz.wahlig@gmail.com>
#
# Distributed under the new BSD license.
#

import ped, ui

# new ped.PythonFileWindow.get_shortcuts classmethod
def get_shortcuts(cls):
    menu = old_get_shortcuts()
    menu.append(ui.MenuItem(_('Comment Line'), method=cls.comment_line))
    return menu

# added ped.PythonFileWindow.comment_line method
def comment_line(self):
    # move the cursor to the start of a line
    self.move_beg_of_line(force=True)

    # check if there are '#' chars at cursor and remove them
    # or add one if there weren't any
    pos = self.body.get_pos()
    if self.body.get(pos, 1) == u'#':
        while self.body.get(pos, 1) == u'#':
            self.body.delete(pos, 1)
    else:
        self.body.add(u'#')
    
    # find the start of next line and go there
    found = False
    for ln, lpos, line in self.get_lines():
        if found:
            pos = lpos
            break
        if lpos == pos:
            found = True

    # move the cursor to the new position
    self.body.set_pos(pos)

if __name__ == '__main__':
    # patch the ped.PythonFileWindow.get_shortcuts classmethod
    old_get_shortcuts = repattr(ped.PythonFileWindow, 'get_shortcuts',
        classmethod(get_shortcuts))
        
    # add the ped.PythonFileWindow.comment_line method
    ped.PythonFileWindow.comment_line = comment_line
