import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide import QtCore, QtGui
from shiboken import wrapInstance
import os

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)

def showDialog( title, message, button=[] ):
    '''
    Shows an error dialog for the user.
    Supply two strings, a title and a message. The message accepts '\n' to break lines.
    If a list of buttons is supplied, the function returns the user input.
    '''
    ret = cmds.confirmDialog( title=title, message=message, button=button )
    if button != []:
        return ret

class PickerButton(QtGui.QPushButton):
    '''
    Button class with added properties to handle bindings to scene nodes
    '''
    def __init__(self, text, parent):
        super(PickerButton, self).__init__(text=text, parent=parent)
        self.sceneNode = None
        self.parentNode = None
        self.mirrorNode = None
        self.rigPart = None

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
        
        modifiers = QtGui.QApplication.keyboardModifiers()
        
        if modifiers == QtCore.Qt.NoModifier:
            for b in self.buttonList:
                b.setChecked(0)
            sender.setChecked(1)
        
        self.selected = [b for b in self.buttonList if b.isChecked()]
            
    def addButton(self):
        '''
        called from: self.addButton_btn
        Adds a new button to the canvas
        
        '''
        b = PickerButton(text='BUTTON', parent=self.canvas)
        b.setCheckable(1)
        b.setStyleSheet('background-color: rgba(0, 255, 0, 175);')
        b.show()
        self.buttonList.append(b)
        b.clicked.connect(self.selectionChanged)
        return b
        
    def duplicateButton(self):
        if len(self.selected) != 1:
            return showDialog('Selection Error', 'Please Select a single button to duplicate')
        b = self.selected[0]
        x = b.x() + 20
        y = b.y() + 20
        width = b.size().width()
        height = b.size().height()
        text = b.text()
        ss = b.styleSheet()
        
        d = self.addButton()
        d.setText(text)
        d.move(x, y)
        d.resize(width, height)
        d.setStyleSheet(ss)
        
    def renameButton(self):
        for b in self.selected:
            b.setText(self.buttonText.text())
        
    def moveLeft(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.move(b.x() - stepSize, b.y())
            
    def moveRight(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.move(b.x() + stepSize, b.y())
            
    def moveUp(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.move(b.x(), b.y() - stepSize)
            
    def moveDown(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.move(b.x(), b.y() + stepSize)
            
    def scaleLeft(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.resize(b.size().width() - stepSize, b.size().height())
            
    def scaleRight(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.resize(b.size().width() + stepSize, b.size().height())
            
    def scaleUp(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.resize(b.size().width(), b.size().height() + stepSize)
            
    def scaleDown(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 10
        else:
            stepSize = 1
        for b in self.selected:
            b.resize(b.size().width(), b.size().height() - stepSize)
        
    def pickColour(self):
        col = self.colourDialog.getColor()
        if col:
            for b in self.selected:
                b.setStyleSheet('background-color: rgba(%s, %s, %s, 175);' % (col.red(), col.green(), col.blue()))
                
    def loadImage(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Select Background Image")
        if os.path.isfile(filename[0]):
            print filename[0]
            self.canvasLabel.setPixmap(QtGui.QPixmap(filename[0]))
            print 'LOADED IMAGE'
    
    def loadBindNodeFromScene(self):
        sel = cmds.ls(sl=1)
        if len(sel)!= 1:
            return showDialog('Selection Error', 'Please select a single scene node')
        
        self.bindNodeText.setText(sel[0])
        
    def bind(self):
        if len(self.selected) != 1:
            return showDialog('Button Error', 'Please select a single button')
        text = self.bindNodeText.text()
        if text:
            if cmds.objExists(text):
                self.selected[0].bindNode = text
                print 'Bound to ' + text
            else:
                return showDialog('Object Error', ('Scene object: ' + text + ' does not exist'))
        else:
            return showDialog('Object Error', 'Please enter the name of a scene node to bind to')
        
    def build(self):
        # get maya main window
        maya = maya_main_window()
        
        # create main window
        self.mainWindow = QtGui.QMainWindow(maya)
        self.mainWindow.setObjectName(self.uiName)
        self.mainWindow.setWindowTitle('Picker Editor')
        self.mainWindow.setMinimumSize(550, 600)
        self.mainWindow.setMaximumSize(550, 600)
        
        # create central widget
        self.centralWidget = QtGui.QWidget()
        self.mainWindow.setCentralWidget(self.centralWidget)
        
        # main layout
        self.mainVLayout = QtGui.QVBoxLayout(self.centralWidget)
        
        # create main horizontal layout
        self.mainHLayout = QtGui.QHBoxLayout()
        self.mainVLayout.addLayout(self.mainHLayout)
        
        # toolbar
        self.toolWidget = QtGui.QWidget()
        self.toolWidget.setFixedSize(120, 500)
        self.mainHLayout.addWidget(self.toolWidget)
        self.toolBar = QtGui.QVBoxLayout(self.toolWidget)
        
        # Canvas
        self.canvas = QtGui.QWidget()
        self.mainHLayout.addWidget(self.canvas)
        
        self.canvasLabel = QtGui.QLabel('TEST_IMAGE', parent=self.canvas)
        self.canvasLabel.setPixmap(QtGui.QPixmap('J:\\CODEBASE\\rooftops\\UI\\bg.png'))
        
        # Tool Buttons
        # Create button
        self.addButton_btn = QtGui.QPushButton('Add Button')
        self.addButton_btn.clicked.connect(self.addButton)
        self.toolBar.addWidget(self.addButton_btn)
        
        #Duplicate button
        self.duplicate_btn = QtGui.QPushButton('Duplicate Button')
        self.duplicate_btn.clicked.connect(self.duplicateButton)
        self.toolBar.addWidget(self.duplicate_btn)
        
        # Button Text
        self.buttonTextLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.buttonTextLayout)
        self.buttonText = QtGui.QLineEdit()
        self.buttonTextLayout.addWidget(self.buttonText)
        self.rename_btn = QtGui.QPushButton('>>>')
        self.rename_btn.clicked.connect(self.renameButton)
        self.buttonTextLayout.addWidget(self.rename_btn)
        
        
        # Move Buttons
        self.moveLabel = QtGui.QLabel('Move Selected')
        self.toolBar.addWidget(self.moveLabel)
        self.moveLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.moveLayout)
        self.moveLeft_btn = QtGui.QPushButton('<')
        self.moveLeft_btn.setFixedSize(20, 40)
        self.moveLayout.addWidget(self.moveLeft_btn)
        self.moveLeft_btn.clicked.connect(self.moveLeft)
        
        self.moveVertLayout = QtGui.QVBoxLayout()
        self.moveLayout.addLayout(self.moveVertLayout)
        self.moveUp_btn = QtGui.QPushButton('^')
        self.moveUp_btn.setFixedSize(40, 20)
        self.moveVertLayout.addWidget(self.moveUp_btn)
        self.moveUp_btn.clicked.connect(self.moveUp)
        
        self.moveDown_btn = QtGui.QPushButton('v')
        self.moveDown_btn.setFixedSize(40, 20)
        self.moveVertLayout.addWidget(self.moveDown_btn)
        self.moveDown_btn.clicked.connect(self.moveDown)
        
        self.moveRight_btn = QtGui.QPushButton('>')
        self.moveRight_btn.setFixedSize(20, 40)
        self.moveLayout.addWidget(self.moveRight_btn)
        self.moveRight_btn.clicked.connect(self.moveRight)
        
        # Scale Buttons
        self.scaleLabel = QtGui.QLabel('Scale Selected')
        self.toolBar.addWidget(self.scaleLabel)
        self.scaleLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.scaleLayout)
        self.scaleLeft_btn = QtGui.QPushButton('-')
        self.scaleLeft_btn.setFixedSize(20, 40)
        self.scaleLayout.addWidget(self.scaleLeft_btn)
        self.scaleLeft_btn.clicked.connect(self.scaleLeft)
        
        self.scaleVertLayout = QtGui.QVBoxLayout()
        self.scaleLayout.addLayout(self.scaleVertLayout)
        self.scaleUp_btn = QtGui.QPushButton('+')
        self.scaleUp_btn.setFixedSize(40, 20)
        self.scaleVertLayout.addWidget(self.scaleUp_btn)
        self.scaleUp_btn.clicked.connect(self.scaleUp)
        
        self.scaleDown_btn = QtGui.QPushButton('-')
        self.scaleDown_btn.setFixedSize(40, 20)
        self.scaleVertLayout.addWidget(self.scaleDown_btn)
        self.scaleDown_btn.clicked.connect(self.scaleDown)
        
        self.scaleRight_btn = QtGui.QPushButton('+')
        self.scaleRight_btn.setFixedSize(20, 40)
        self.scaleLayout.addWidget(self.scaleRight_btn)
        self.scaleRight_btn.clicked.connect(self.scaleRight)
        
        #Color picker button
        self.colour_btn = QtGui.QPushButton('Button Colour')
        self.colour_btn.clicked.connect(self.pickColour)
        self.toolBar.addWidget(self.colour_btn)
        
        # Background image button
        self.image_btn = QtGui.QPushButton('BG Image')
        self.toolBar.addWidget(self.image_btn)
        self.image_btn.clicked.connect(self.loadImage)
        
        #Color Dialog
        self.colourDialog = QtGui.QColorDialog(parent=maya)
        
        # Binding tools
        self.bindLabel = QtGui.QLabel('Bind to Ctrl')
        self.mainVLayout.addWidget(self.bindLabel)
        self.bindNodeLayout = QtGui.QHBoxLayout()
        self.mainVLayout.addLayout(self.bindNodeLayout)
        self.bindNodeText = QtGui.QLineEdit()
        self.loadBindNode_btn = QtGui.QPushButton('<<<')
        self.bind_btn = QtGui.QPushButton('Bind')
        self.bindNodeLayout.addWidget(self.bindNodeText)
        self.bindNodeLayout.addWidget(self.loadBindNode_btn)
        self.bindNodeLayout.addWidget(self.bind_btn)
        
        self.loadBindNode_btn.clicked.connect(self.loadBindNodeFromScene)
        self.bind_btn.clicked.connect(self.bind)
        
        self.mainWindow.show()
        
        
