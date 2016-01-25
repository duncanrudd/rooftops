__author__ = 'drudd'

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide import QtCore, QtGui
from shiboken import wrapInstance
import os
import xml.etree.ElementTree as et
from xml.dom import minidom
import json

def prettyPrint(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = et.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

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
        self.sceneNode = ''
        self.parentNode = ''
        self.mirrorNode = ''
        self.rigPart = ''
        self.defaults={}

class PickerEditor(QtGui.QWidget):
    def __init__(self):
        super(PickerEditor, self).__init__()
        self.uiName = 'pickerEditor'
        self.delete()
        self.buttonList = []
        self.selected = []
        self.tabs = []
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

    def addNewTab(self, tabName='New Tab'):
        '''
        Adds a new tab to the canvas
        '''
        canvasLabel = QtGui.QLabel('')
        canvasLabel.setFixedSize(400, 500)
        self.canvas.setAutoFillBackground(True)
        p = canvasLabel.palette()
        p.setColor(canvasLabel.backgroundRole(), 'white')
        canvasLabel.setPalette(p)
        t = self.canvas.addTab(canvasLabel, tabName)
        self.tabs.append({'tab':t, 'bg':''})
        return t

    def deleteTab(self):
        '''
        Removes the currently visible tab from the canvas
        '''
        del self.tabs[self.canvas.currentIndex()]
        currentTab = self.canvas.currentWidget()
        currentTab.deleteLater()

    def renameTab(self):
        self.canvas.setTabText(self.canvas.currentIndex(), self.tabText.text())

    def addButton(self):
        '''
        called from: self.addButton_btn
        Adds a new button to the canvas
        '''
        b = PickerButton(text='BUTTON', parent=self.canvas.currentWidget())
        b.setCheckable(1)
        b.setStyleSheet('background-color: rgba(0, 255, 0, 175);')
        b.show()
        self.buttonList.append(b)
        b.clicked.connect(self.selectionChanged)
        return b

    def deleteButton(self):
        for b in self.selected:
            del self.buttonList[self.buttonList.index(b)]
            b.deleteLater()

    def duplicateButton(self):
        if len(self.selected) != 1:
            return showDialog('Selection Error', 'Please Select a single button to duplicate')
        b = self.selected[0]
        attrDict = self.getButtonData(b)
        attrDict['xPos']  = str(int(attrDict['xPos']) + 20)
        attrDict['yPos']  = str(int(attrDict['yPos']) + 20)

        d = self.addButton()
        self.setButtonData(d, attrDict)

    def renameButton(self):
        for b in self.selected:
            b.setText(self.buttonText.text())

    def moveLeft(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.move(b.x() - stepSize, b.y())

    def moveRight(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.move(b.x() + stepSize, b.y())

    def moveUp(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.move(b.x(), b.y() - stepSize)

    def moveDown(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.move(b.x(), b.y() + stepSize)

    def scaleLeft(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.resize(b.size().width() - stepSize, b.size().height())

    def scaleRight(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.resize(b.size().width() + stepSize, b.size().height())

    def scaleUp(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.resize(b.size().width(), b.size().height() + stepSize)

    def scaleDown(self):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            stepSize = 50
        elif modifiers == QtCore.Qt.ControlModifier:
            stepSize = 1
        else:
            stepSize = 10
        for b in self.selected:
            b.resize(b.size().width(), b.size().height() - stepSize)

    def pickColour(self):
        col = self.colourDialog.getColor()
        if col:
            for b in self.selected:
                b.setStyleSheet('background-color: rgba(%s, %s, %s, 175);' % (col.red(), col.green(), col.blue()))

    def loadImage(self, image=None):
        if image:
            self.tabs[self.canvas.currentIndex()]['bg'] = image
        else:
            self.tabs[self.canvas.currentIndex()]['bg'] = QtGui.QFileDialog.getOpenFileName(self, "Select Background Image")[0]
        if os.path.isfile(self.tabs[self.canvas.currentIndex()]['bg']):
            print self.tabs[self.canvas.currentIndex()]['bg']
            self.canvas.currentWidget().setPixmap(QtGui.QPixmap(self.tabs[self.canvas.currentIndex()]['bg']))
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
                self.selected[0].sceneNode = text
                print 'Bound to ' + text
            else:
                return showDialog('Object Error', ('Scene object: ' + text + ' does not exist'))
        else:
            return showDialog('Object Error', 'Please enter the name of a scene node to bind to')

    def setDefaults(self):
        '''
        Populates the defaults dictionary on selected buttons.
        Makes a dictionary key for each keyable attribute and stores the current value
        '''
        for btn in self.selected:
            if btn.sceneNode:
                btn.defaults = {}
                for attr in cmds.listAttr(btn.sceneNode, k=1, u=1):
                    btn.defaults[attr] = cmds.getAttr(btn.sceneNode + '.' + attr)

            print btn.defaults

    def getButtonData(self, button, bindings=0):
        '''
        Returns a dictionary with the supplied button's data
        If the bindings flag is set, also returns the scene node bindings

        '''
        attrDict = {}
        attrDict['xPos'] = str(button.x())
        attrDict['yPos'] = str(button.y())
        attrDict['width'] = str(button.size().width())
        attrDict['height'] = str(button.size().height())
        attrDict['style'] = str(button.styleSheet())
        attrDict['text'] = button.text()

        if bindings:
            attrDict['sceneNode'] = button.sceneNode
            attrDict['parentNode'] = button.parentNode
            attrDict['mirrorNode'] = button.mirrorNode
            attrDict['rigPart'] = button.rigPart
            attrDict['defaults'] = json.dumps(button.defaults)

        return attrDict

    def setButtonData(self, button, attrDict, bindings=0):
        button.setText(attrDict['text'])
        button.move(int(attrDict['xPos']), int(attrDict['yPos']))
        button.resize(int(attrDict['width']), int(attrDict['height']))
        button.setStyleSheet(attrDict['style'])

        if bindings:
            button.sceneNode = attrDict['sceneNode']
            button.parentNode = attrDict['parentNode']
            button.mirrorNode = attrDict['mirrorNode']
            button.rigPart = attrDict['rigPart']
            button.defaults = json.loads(attrDict['defaults'])

    def save(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save Picker")[0]

        # Xml root element
        root = et.Element('picker')
        root.set('version', '1.0')

        # Get Tabs
        tabs = et.SubElement(parent=root, tag='tabs')
        for i in range(self.canvas.count()):
            t = et.SubElement(parent=tabs, tag='tab', label=self.canvas.tabText(i))

            # Gather button info
            buttons = et.SubElement(parent=t, tag='buttons')
            for b in self.canvas.widget(i).children():
                e = et.SubElement(parent=buttons, tag='btn', attrib=self.getButtonData(b, bindings=1))

            # BG image
            bg = et.SubElement(parent=t, tag='bg', file=self.tabs[i]['bg'])

        # Xml tree
        open(filename, 'w').write(prettyPrint(root))
        print 'saving: ' + filename

    def clearCanvas(self):
        self.canvas.clear()
        self.buttonList = []
        self.selected = []
        self.tabs = []

    def load(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Load Picker")[0]
        tree = et.parse(filename)
        if not tree:
            return showDialog('File Error', ('File not found: ' + filename))

        self.clearCanvas()
        root = tree.getroot()
        tabs = root.find('tabs')
        for tab in tabs:
            t = self.addNewTab(tab.get('label'))
            self.canvas.setCurrentIndex(t)
            buttons = tab.find('buttons')
            for btn in buttons:
                b = self.addButton()
                self.setButtonData(b, btn.attrib, bindings=1)
            self.loadImage(image=tab.find('bg').get('file'))
            print 'loading: ' + filename

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
        '''
        self.canvas = QtGui.QWidget()
        self.canvas.setFixedSize(400, 500)
        self.canvas.setAutoFillBackground(True)
        p = self.canvas.palette()
        p.setColor(self.canvas.backgroundRole(), 'white')
        self.canvas.setPalette(p)
        self.mainHLayout.addWidget(self.canvas)

        self.canvasLabel = QtGui.QLabel('', parent=self.canvas)
        self.canvasLabel.setFixedSize(400, 500)
        '''
        self.canvas = QtGui.QTabWidget()
        self.canvas.setFixedSize(400, 520)
        self.mainHLayout.addWidget(self.canvas)

        self.addNewTab()

        # Tool Buttons
        # Create Tab
        self.addTab_btn = QtGui.QPushButton('Add Tab')
        self.addTab_btn.clicked.connect(self.addNewTab)
        self.toolBar.addWidget(self.addTab_btn)

        # Tab Text
        self.tabTextLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.tabTextLayout)
        self.tabText = QtGui.QLineEdit()
        self.tabTextLayout.addWidget(self.tabText)
        self.renameTab_btn = QtGui.QPushButton('>>>')
        self.renameTab_btn.clicked.connect(self.renameTab)
        self.tabTextLayout.addWidget(self.renameTab_btn)

        # Remove Tab
        self.deleteTab_btn = QtGui.QPushButton('Delete Tab')
        self.deleteTab_btn.clicked.connect(self.deleteTab)
        self.toolBar.addWidget(self.deleteTab_btn)

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

        # Remove Button
        self.delete_btn = QtGui.QPushButton('Delete Button')
        self.toolBar.addWidget(self.delete_btn)
        self.delete_btn.clicked.connect(self.deleteButton)

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

        # Set Defaults
        self.defaults_btn = QtGui.QPushButton('Set Defaults')
        self.toolBar.addWidget(self.defaults_btn)
        self.defaults_btn.clicked.connect(self.setDefaults)

        # IO buttons
        self.fileLayout = QtGui.QHBoxLayout()
        self.toolBar.addLayout(self.fileLayout)
        self.save_btn = QtGui.QPushButton('Save')
        self.fileLayout.addWidget(self.save_btn)
        self.save_btn.clicked.connect(self.save)
        self.load_btn = QtGui.QPushButton('Load')
        self.fileLayout.addWidget(self.load_btn)
        self.load_btn.clicked.connect(self.load)

        # stretch to push buttons up
        self.toolBar.addStretch(1)

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

class Picker(QtGui.QWidget):
    def __init__(self):
        super(Picker, self).__init__()
        self.uiName = 'Picker'
        self.delete()
        self.buttonList = []
        self.selected = []
        self.tabs = []
        self.build()

    def delete(self):
        #check to see if the ui already exists and, if so, delete it
        if cmds.window(self.uiName, exists=True):
            cmds.deleteUI(self.uiName, wnd=True)

    def getScenePickers(self):
        self.pickerPath = os.path.join(os.path.dirname(__file__), 'pickers\\')
        pickers = [f for f in os.listdir(self.pickerPath) if '_picker.xml' in f]
        refPickers = [p for p in pickers if cmds.namespace(exists=(':' + p.replace('_picker.xml', '')))]
        refPickers.append('CAMERA')
        localPickers = [p for p in pickers if ('|' + p.replace('_picker.xml', '')) in cmds.ls(long=1)]
        scenePickers = refPickers + localPickers
        return [p.replace('_picker.xml', '') for p in scenePickers]

    def setButtonData(self, button, attrDict):
        button.setText(attrDict['text'])
        button.move(int(attrDict['xPos']), int(attrDict['yPos']))
        button.resize(int(attrDict['width']), int(attrDict['height']))
        button.setStyleSheet(attrDict['style'])

        button.sceneNode = attrDict['sceneNode']
        button.parentNode = attrDict['parentNode']
        button.mirrorNode = attrDict['mirrorNode']
        button.rigPart = attrDict['rigPart']
        button.defaults = json.loads(attrDict['defaults'])

    def selectionChanged(self):
        sender = self.sender()

        modifiers = QtGui.QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.NoModifier:
            for b in self.buttonList:
                b.setChecked(0)
            sender.setChecked(1)

        self.selected = [b for b in self.buttonList if b.isChecked()]
        selList = [b.sceneNode for b in self.selected if b.sceneNode]
        if selList:
            cmds.select(selList)

    def addButton(self, parent):
        '''
        called from: self.addButton_btn
        Adds a new button to the canvas
        '''
        b = PickerButton(text='', parent=parent)
        b.setCheckable(1)
        b.show()
        self.buttonList.append(b)
        b.clicked.connect(self.selectionChanged)
        return b

    def addNewTab(self, parent, tabName=''):
        '''
        Adds a new tab to the canvas
        '''
        canvasLabel = QtGui.QLabel('')
        canvasLabel.setFixedSize(400, 500)
        canvasLabel.setAutoFillBackground(True)
        p = canvasLabel.palette()
        p.setColor(canvasLabel.backgroundRole(), 'white')
        canvasLabel.setPalette(p)
        t = parent.addTab(canvasLabel, tabName)
        self.tabs.append({'tab':t, 'bg':''})
        return t

    def load(self, filename, parent, asset):
        print filename
        tree = et.parse(filename)
        if not tree:
            return showDialog('File Error', ('File not found: ' + filename))
        root = tree.getroot()
        tabs = root.find('tabs')

        for tab in tabs:
            t = self.addNewTab(parent = parent, tabName=tab.get('label'))
            parent.setCurrentIndex(t)
            panel = parent.currentWidget()
            buttons = tab.find('buttons')
            for btn in buttons:
                b = self.addButton(panel)
                self.setButtonData(b, btn.attrib)

                # if the asset is in a namespace, add the asset name to the sceneNode
                if cmds.namespace(exists=(':' + asset)):
                    b.sceneNode = asset + ':' + b.sceneNode

            bg = tab.find('bg').get('file')
            if bg:
                if os.path.exists(bg):
                    panel.setPixmap(QtGui.QPixmap(bg))

        parent.setCurrentIndex(0)

    def zero(self):
        '''
        resets keyable attributes on the sceneNodes of selected buttons to their stored default values
        '''
        cmds.undoInfo(openChunk=1)
        for button in self.selected:
            if button.sceneNode:
                for attr in button.defaults.keys():
                    cmds.setAttr(button.sceneNode + '.' + attr, button.defaults[attr])
        cmds.undoInfo(closeChunk=1)

    def selectAll(self):
        '''
        selects all controls that have buttons in the picker
        '''
        self.selected = [b for b in self.canvas.currentWidget().currentWidget().children()]
        for b in self.buttonList:
            b.setChecked(0)
        for b in self.selected:
            b.setChecked(1)

        selList = [b.sceneNode for b in self.selected if b.sceneNode]
        print selList
        if selList:
            cmds.select(selList)

    def getRoot(self, node=None):
        if not node and len(cmds.ls(sl=1)) > 0:
            node = cmds.ls(sl=1)[0]

        fullPath = cmds.ls(node, l=1)[0]
        root = fullPath.split('|')[1]
        return root

    def getControls(self, root, stringID='CON'):
        curves = cmds.listRelatives(root, ad=1, type='nurbsCurve')
        controls = []
        for curve in curves:
            parent = cmds.listRelatives(curve, p=1, type='transform')[0]
            #if cmds.attributeQuery('con_category', node=parent, exists=1):
            if parent.endswith('_ctrl'):
                if not cmds.listConnections(parent, type='constraint', d=0):
                    controls.append(parent)
        return controls

    def selectRig(self):
        cmds.select(self.getControls(root=self.getRoot()))

    def linkToBlank(self):
        '''
        Binds the 'CAM' tab to the namespace of the currently selected camera.
        '''
        if not cmds.ls(sl=1):
            return showDialog('Selection Error', 'Select a rig control to bind')
        theNameSpace = cmds.ls(sl=1)[0].split(':')[0]
        if theNameSpace:
            panel = self.canvas.widget(self.canvas.count() - 1)
            for index in range(panel.count()):
                buttons = panel.widget(index).children()
                self.buttonList = [b for b in self.buttonList if not b in buttons]
                panel.widget(index).deleteLater()
            self.canvas.setTabText(self.canvas.count() - 1, theNameSpace)
            self.load(self.pickerPath + 'CAMERA_picker.xml', panel, theNameSpace)

    def build(self):
    # get maya main window
        maya = maya_main_window()

        # create main window
        self.mainWindow = QtGui.QMainWindow(maya)
        self.mainWindow.setObjectName(self.uiName)
        self.mainWindow.setWindowTitle('Character Picker')
        self.mainWindow.setMinimumSize(420, 620)
        self.mainWindow.setMaximumSize(420, 620)

        # create central widget
        self.centralWidget = QtGui.QWidget()
        self.mainWindow.setCentralWidget(self.centralWidget)

        # main layout
        self.mainVLayout = QtGui.QVBoxLayout(self.centralWidget)

        # Canvas
        self.canvas = QtGui.QTabWidget()
        self.canvas.setFixedSize(400, 540)
        self.mainVLayout.addWidget(self.canvas)

        for asset in self.getScenePickers():
            print 'found asset: ' + asset
            assetTab = QtGui.QTabWidget()
            assetTab.setFixedSize(400, 520)
            t = self.canvas.addTab(assetTab, asset)
            self.canvas.setCurrentIndex(t)
            self.load(self.pickerPath +asset+'_picker.xml', self.canvas.currentWidget(), asset)

        # Select All buttons
        self.selectAllHLayout = QtGui.QHBoxLayout()
        self.mainVLayout.addLayout(self.selectAllHLayout)
        self.all_btn = QtGui.QPushButton('SELECT ALL')
        self.all_btn.clicked.connect(self.selectAll)
        self.selectAllHLayout.addWidget(self.all_btn)
        self.all_rig_btn = QtGui.QPushButton('SELECT RIG')
        self.all_rig_btn.clicked.connect(self.selectRig)
        self.selectAllHLayout.addWidget(self.all_rig_btn)

		# Zero button and bind button
        self.zeroHLayout = QtGui.QHBoxLayout()
        self.mainVLayout.addLayout(self.zeroHLayout)
        self.zero_btn = QtGui.QPushButton('ZERO')
        self.zero_btn.clicked.connect(self.zero)
        self.zeroHLayout.addWidget(self.zero_btn)
        self.link_btn = QtGui.QPushButton('LINK CAM')
        self.link_btn.clicked.connect(self.linkToBlank)
        self.zeroHLayout.addWidget(self.link_btn)

        self.mainWindow.show()
