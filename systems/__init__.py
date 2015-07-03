import os
import rooftops as rt

#add subdirectories you want to import here
dirList = []

path = os.path.dirname(os.path.realpath(__file__))

importList = rt.getImportList( path, dirList )

for module in importList:
    mod = __import__(module, globals(), locals())
    reload(mod)
    print '%s imported successfully' % module
