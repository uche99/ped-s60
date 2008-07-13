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

import sys, e32, ped, ui

# new ped.PythonFileWindow.control_key_press method
def control_key_press(self, key):
    # check if the configured shortkey was pressed
    if key == ped.app.settings.plugins.comments_key:
        # move the cursor to the start of a line
        self.move_beg_of_line(force=True)

        # check if there are '#' chars at cursor and remove them
        # or add one if there wren't any
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

        # we have handled the key
        return True
    else:
        # let the old method control other keys
        return old_control_key_press(self, key)

if __name__ == '__main__':
    # patch the ped.PythonFileWindow.control_key_press method
    old_control_key_press = repattr(ped.PythonFileWindow,
        'control_key_press', control_key_press)

    # add to settings
    ped.app.settings.plugins.add('comments_key',
        ui.ShortkeySetting(_('Comments key'), ui.EKey2))
