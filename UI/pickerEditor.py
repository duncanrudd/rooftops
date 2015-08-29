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
        self.selected = []
        self.build()
        
    def delete(self):
        #check to see if the ui already exists and, if so, delete it
        if cmds.window(self.uiName, exists=True):
            cmds.deleteUI(self.uiName, wnd=True)
            
    def selectionChanged(self):
        sender = self.sender()
        if not sender in self.selected:
            self.selected.append(sender)
        if len(self.selected) == 1:
            self.moveX_spinBox.setValue(sender.pos().x())
            self.moveY_spinBox.setValue(sender.pos().y())
            self.sizeX_spinBox.setValue(sender.width())
            self.sizeY_spinBox.setValue(sender.height())
        else:
            self.moveX_spinBox.setValue(0)
            self.moveY_spinBox.setValue(0)
            self.sizeX_spinBox.setValue(0)
            self.sizeY_spinBox.setValue(0)
        
        modifiers = QtGui.QApplication.keyboardModifiers()
        
        #if modifiers == QtCore.Qt.ShiftModifier:
        if modifiers == QtCore.Qt.NoModifier:
            for b in self.buttonList:
                b.setChecked(0)
            sender.setChecked(1)
            
        
    
    def addButton(self):
        '''
        called from: self.addButton_btn
        Adds a new button to the canvas
        
        '''
        b = QtGui.QPushButton('BUTTON', parent=self.canvas)
        b.setCheckable(1)
        b.setStyleSheet('background-color: rgba(0, 255, 0, 75%);')
        b.show()
        self.buttonList.append(b)
        self.selected = [b]
        b.clicked.connect(self.selectionChanged)
        
    def moveButton(self):
        if len(self.selected) == 1:
            pos = QtCore.QPoint()
            pos.setX(self.moveX_spinBox.value())
            pos.setY(self.moveY_spinBox.value())
            self.selected[-1].move(pos)
        elif len(self.selected) > 1:
            for b in self.selected:
                b.move(b.x() + self.moveX_spinBox.value(), b.y() + self.moveY_spinBox.value())
        
    def sizeButton(self):
        x = self.sizeX_spinBox.value()
        y = self.sizeY_spinBox.value()
        self.selected[-1].resize(x, y)
        
    def pickColour(self):
        col = self.colourDialog.getColor()
        if col:
            self.selected[-1].setStyleSheet('background-color: rgb(%s, %s, %s);' % (col.red(), col.green(), col.blue()))
        
        
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
        self.moveX_spinBox.editingFinished.connect(self.moveButton)

        self.moveY_spinBox = QtGui.QSpinBox()
        self.moveY_spinBox.setMaximum(450)
        self.moveLayout.addWidget(self.moveY_spinBox)
        self.moveY_spinBox.editingFinished.connect(self.moveButton)
        
        # scale spinBox
        self.size_label = QtGui.QLabel('Size: x, y')
        self.toolBar.addWidget(self.size_label)
        
        self.sizeLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.sizeLayout)
        self.sizeX_spinBox = QtGui.QSpinBox()
        self.sizeX_spinBox.setMaximum(300)
        self.sizeLayout.addWidget(self.sizeX_spinBox)
        self.sizeX_spinBox.editingFinished.connect(self.sizeButton)

        self.sizeY_spinBox = QtGui.QSpinBox()
        self.sizeY_spinBox.setMaximum(450)
        self.sizeLayout.addWidget(self.sizeY_spinBox)
        self.sizeY_spinBox.editingFinished.connect(self.sizeButton)
        
        #Color picker button
        self.colour_btn = QtGui.QPushButton('Button Colour')
        self.colour_btn.clicked.connect(self.pickColour)
        self.toolBar.addWidget(self.colour_btn)
        
        #Color Dialog
        self.colourDialog = QtGui.QColorDialog(parent=maya)
        
        self.mainWindow.show()
        
        
