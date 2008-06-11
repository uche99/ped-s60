try:

    import ped

    if __name__ == '__main__':
        ped.app.start()

except:

    import sys, traceback, appuifw

    appuifw.app.title = u'Fatal Error'
    appuifw.app.screen = 'normal'
    appuifw.app.focus = None
    appuifw.app.body = appuifw.Text()
    appuifw.app.exit_key_handler = appuifw.app.set_exit
    appuifw.app.menu = [(u'Exit', appuifw.app.set_exit)]
    appuifw.app.body.set(unicode(''.join(traceback.format_exception(*sys.exc_info()))))
