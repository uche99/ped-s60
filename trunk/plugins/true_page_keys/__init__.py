#
# true_page_keys
#
# Ped plugin replacing the standard page-up/down emulation
# with a true page-up/down functions by simulating the
# true page-up/down keypresses. Uses the "keypress" module
# which has to be installed separately.
#
# Copyright (c) 2008, Arkadiusz Wahlig
# <arkadiusz.wahlig@gmail.com>
#
# Distributed under the new BSD license.
#

import ped, e32
import keypress
from key_codes import *

def page_up(self):
    keypress.simulate_key(EKeyPageUp, EStdKeyPageUp)
    e32.ao_yield()

def page_down(self):
    keypress.simulate_key(EKeyPageDown, EStdKeyPageDown)
    e32.ao_yield()

# remove unneeded settings
ped.app.settings.text.remove('pagesizeport')
ped.app.settings.text.remove('pagesizefull')
ped.app.settings.text.remove('pagesizeland')

# replace old methods with our
setattr(ped.TextWindow, 'move_page_up', page_up)
setattr(ped.TextWindow, 'move_page_down', page_down)
