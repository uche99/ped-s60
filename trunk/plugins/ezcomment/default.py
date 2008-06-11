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

import sys
import os
import ped
import ui

# our new ped.PythonFileWindow.control_key_press method
def control_key_press(self, key):
    # check if the configured shortkey was pressed
    if key == ped.app.settings['ezcomment_key'].get():
        # move the cursor to the start of a line
        self.move_beg_of_line()
        
        # check if there are '#' chars at cursor and remove them
        # or add one if there wren't any
        pos = self.body.get_pos()
        while True:
            char = self.body.get(pos, 1)
            if char == '#':
                self.body.delete(pos, 1)
            else:
                self.body.add(u'#')
                break
        
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
        # let the old method control the key
        return old_control_key_press(self, key)

def apply_settings(self):
    oldlang = self.language
    old_apply_settings(self)
    if self.language != oldlang:
        _.load(os.path.join(path, 'lang\\%s' % self.language.encode('utf8')))

if __name__ == '__main__':
    # plugin path
    path = os.path.split(sys.argv[0])[0]

    # i18n object
    _ = ui.Translator()
    if ped.app.language != u'English':
        _.load(os.path.join(path, 'lang\\%s' % ped.app.language.encode('utf8')))

    # patch the ped.PythonFileWindow.control_key_press method
    old_control_key_press = ped.repattr(ped.PythonFileWindow,
        'control_key_press', control_key_press)

    # patch the ped.Application.apply_settings method
    old_apply_settings = ped.repattr(ped.Application,
        'apply_settings', apply_settings)

    # add the shortkey configuration to the settings
    ped.app.settings.add_setting('misc', 'ezcomment_key',
        ui.ShortkeySetting(_('EZ-Comment key'), ui.EKey2))
