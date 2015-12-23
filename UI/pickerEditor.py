import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide import QtCore, QtGui
from shiboken import wrapInstance

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)
    
class PickerEditor(QtGui.QWidget):
    def __init__(self):
        super(PickerEditor, self).__init__()
        self.uiName = 'pickerEditor'
        self.delete()
        self.buttonList = []
        self.switch = 1
        self.build()
        
    def delete(self):
        #check to see if the ui already exists and, if so, delete it
        if cmds.window(self.uiName, exists=True):
            cmds.deleteUI(self.uiName, wnd=True)
            
    def selectionChanged(self):
        self.selected = self.sender()
        self.switch = 0
        self.moveX_spinBox.setValue(self.sender().pos().x())
        self.switch = 0
        self.moveY_spinBox.setValue(self.sender().pos().y())
        self.switch = 0
        self.sizeX_spinBox.setValue(self.sender().width())
        self.switch = 0
        self.sizeY_spinBox.setValue(self.sender().height())
        
    
    def addButton(self):
        '''
        called from: self.addButton_btn
        Adds a new button to the canvas
        
        '''
        b = QtGui.QPushButton('BUTTON', parent=self.canvas)
        b.show()
        self.buttonList.append(b)
        self.selected = b
        b.clicked.connect(self.selectionChanged)
        
    def moveButton(self):
        if self.switch:
            pos = QtCore.QPoint()
            pos.setX(self.moveX_spinBox.value())
            pos.setY(self.moveY_spinBox.value())
            self.selected.move(pos)
        self.switch = 1
        
    def sizeButton(self):
        if self.switch:
            x = self.sizeX_spinBox.value()
            y = self.sizeY_spinBox.value()
            self.selected.resize(x, y)
        self.switch = 1
        
    def pickColour(self):
        col = self.colourDialog.getColor()
        if col:
            self.selected.setStyleSheet('background-color: rgb(%s, %s, %s);' % (col.red(), col.green(), col.blue()))
        
        
    def build(self):
       # get maya main window
        maya = maya_main_window()
        
        # create main window
        self.mainWindow = QtGui.QMainWindow(maya)
        self.mainWindow.setObjectName(self.uiName)
        self.mainWindow.setWindowTitle('Picker Editor')
        self.mainWindow.setMinimumSize(450, 500)
        self.mainWindow.setMaximumSize(450, 500)
        
        # create central widget
        self.centralWidget = QtGui.QWidget()
        self.mainWindow.setCentralWidget(self.centralWidget)
        
        # create main layout
        self.mainLayout = QtGui.QHBoxLayout(self.centralWidget)
        
        # toolbar
        self.toolWidget = QtGui.QWidget()
        self.toolWidget.setFixedWidth(120)
        self.mainLayout.addWidget(self.toolWidget)
        self.toolBar = QtGui.QVBoxLayout(self.toolWidget)
        
        # Canvas
        self.canvas = QtGui.QWidget()
        self.canvas.setAutoFillBackground(True)
        p = self.canvas.palette()
        p.setColor(self.canvas.backgroundRole(), 'white')
        self.canvas.setPalette(p)
        self.mainLayout.addWidget(self.canvas)
        
        # Tool Buttons
        # Create button
        self.addButton_btn = QtGui.QPushButton('Add Button')
        self.addButton_btn.clicked.connect(self.addButton)
        self.toolBar.addWidget(self.addButton_btn)
        
        # move spinBox
        self.move_label = QtGui.QLabel('Move: x, y')
        self.toolBar.addWidget(self.move_label)
        
        self.moveLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.moveLayout)
        self.moveX_spinBox = QtGui.QSpinBox()
        self.moveX_spinBox.setMaximum(300)
        self.moveLayout.addWidget(self.moveX_spinBox)
        self.moveX_spinBox.valueChanged.connect(self.moveButton)

        self.moveY_spinBox = QtGui.QSpinBox()
        self.moveY_spinBox.setMaximum(450)
        self.moveLayout.addWidget(self.moveY_spinBox)
        self.moveY_spinBox.valueChanged.connect(self.moveButton)
        
        # scale spinBox
        self.size_label = QtGui.QLabel('Size: x, y')
        self.toolBar.addWidget(self.size_label)
        
        self.sizeLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.sizeLayout)
        self.sizeX_spinBox = QtGui.QSpinBox()
        self.sizeX_spinBox.setMaximum(300)
        self.sizeLayout.addWidget(self.sizeX_spinBox)
        self.sizeX_spinBox.valueChanged.connect(self.sizeButton)

        self.sizeY_spinBox = QtGui.QSpinBox()
        self.sizeY_spinBox.setMaximum(450)
        self.sizeLayout.addWidget(self.sizeY_spinBox)
        self.sizeY_spinBox.valueChanged.connect(self.sizeButton)
        
        #Color picker button
        self.colour_btn = QtGui.QPushButton('Button Colour')
        self.colour_btn.clicked.connect(self.pickColour)
        self.toolBar.addWidget(self.colour_btn)
        
        #Color Dialog
        self.colourDialog = QtGui.QColorDialog(parent=maya)
        
        self.mainWindow.show()
        
        
