#
# system_app
#
# Ped plugin making it a system application using the "envy" module
# (has to be installed separately). Configurable.
#
# Copyright (c) 2008, Arkadiusz Wahlig
# <arkadiusz.wahlig@gmail.com>
#
# Distributed under the new BSD license.
#

import sys, ped, ui

try:
    from envy import set_app_system
except ImportError:
    sys.exit('%s plugin requires envy module' % __plugin__)

def apply_settings(self):
    old_apply_settings(self)
    set_app_system(self.settings.plugins.system_app)

# get the translator object for this plugin
_ = ped.get_plugin_translator(__file__)

# patch the ped.Application.apply_settings method
old_apply_settings = ped.repattr(ped.Application,
    'apply_settings', apply_settings)

# add to settings
ped.app.settings.plugins.append('system_app',
    ui.BoolSetting(_('System application'), False))
