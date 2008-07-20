import ped, e32
import keypress
from key_codes import *

def page_up(self):
    keypress.simulate_key(EKeyPageUp, EStdKeyPageUp)
    e32.ao_yield()

def page_down(self):
    keypress.simulate_key(EKeyPageDown, EStdKeyPageDown)
    e32.ao_yield()

if __name__ == '__main__':
    ped.app.settings.editor.remove('pagesizenorm')
    ped.app.settings.editor.remove('pagesizefull')
    ped.app.settings.editor.remove('pagesizeland')
    
    setattr(ped.TextWindow, 'move_page_up', page_up)
    setattr(ped.TextWindow, 'move_page_down', page_down)
