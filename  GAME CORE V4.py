try:

    import sys
    sys.path.append("E:\Python")
    import summonnight

except:

    import sys
    sys.path.append("E:\Python")
    import summonnight
    appuifw.app.body.set(unicode(''.join(traceback.format_exception(*sys.exc_info()))))
