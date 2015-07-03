import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide import QtCore, QtGui
from shiboken import wrapInstance

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)

class PickerGui(object):
    '''
    Gui for selecting rig controls and calling functions on them
    '''
    def __init__(self):
        self.uiName = 'pickerGui'
        self.delete()
        self.rigData = self.getRigData()
        self.buttonList = []
        self.sceneRigs = self.getSceneRigs()
        self.build()
        
    def delete(self):
        #check to see if the ui already exists and, if so, delete it
        if cmds.window(self.uiName, exists=True):
            cmds.deleteUI(self.uiName, wnd=True)
            
    def getRigData(self):
        # Collect metadata from rig controls to determin button appearance and functionality
        rigData = [
                        {'label':'button1', 'pos':[0,0], 'size':[50,30], 'colour':[255,0,0]},
                        {'label':'button2', 'pos':[50,0], 'size':[30,50], 'colour':[0,255,0]}
                    ]
        return rigData
    
    def getSceneRigs(self):
        '''
        Collect all metaRigs in the scene by checking for 'metaRigName' attribute
        
        '''
        sceneRigs = [node for node in cmds.ls() if cmds.attributeQuery('metaRigName', node=node, exists=1)]
        print 'Metarigs found: %s' % sceneRigs
        return sceneRigs
            
        
    
    def build(self):
        # get maya main window
        maya = maya_main_window()
        
        # creae main window
        self.mainWindow = QtGui.QMainWindow(maya)
        self.mainWindow.setObjectName(self.uiName)
        self.mainWindow.setWindowTitle('Picker GUI')
        self.mainWindow.setMinimumSize(250, 400)
        self.mainWindow.setMaximumSize(250, 400)
        
        # create central widget
        self.centralWidget = QtGui.QWidget()
        self.mainWindow.setCentralWidget(self.centralWidget)
        
        # Main layout
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        
        # Button widget
        self.buttonWidget = QtGui.QWidget()
        self.mainLayout.addWidget(self.buttonWidget)
        
        # ComboBox
        self.sceneRigsComboBox = QtGui.QComboBox()
        self.mainLayout.addWidget(self.sceneRigsComboBox)
        self.sceneRigsComboBox.addItems([cmds.getAttr('%s.metaRigName' % rig) for rig in self.sceneRigs])
        
        # Buttons
        for button in self.rigData:
            b = QtGui.QPushButton(button['label'], parent=self.buttonWidget)
            b.setStyleSheet('background-color: rgb(%s, %s, %s);' % (button['colour'][0], button['colour'][1], button['colour'][2]))
            b.setGeometry(button['pos'][0], button['pos'][1], button['size'][0], button['size'][1])

        
        
        self.mainWindow.show()