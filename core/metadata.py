import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide import QtCore, QtGui
from shiboken import wrapInstance

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)
import json

# Colours for buttons on gui - default values: right-red, centre-green, left-blue
colourList=[[0,255,0], [0,0,255], [255,0,0]]

######################################################################################################################################################

def align( node=None, target=None, translate=True, orient=True ):
    '''
    sets the translation and / or orientation of node to match target
    
    '''
    
    # Validate that the correct arguments have been supplied
    if not node or not target:
        # If node and target aren't explicitly supplied, check for a valid selection to use 
        sel = cmds.ls(sl=1, type='transform')
        if len( sel ) == 2:
            node, target = sel[0], sel[1]
        else:
            return 'Argument Error, Cannot determine nodes to align'

    targetMatrix = cmds.xform( target, q=True, ws=1, matrix=True )
    nodeMatrix = cmds.xform( node, q=True, ws=1, matrix=True )
    
    if translate and orient:
        cmds.xform ( node, ws=1, matrix=targetMatrix )
    elif translate:
        # set row4 x y z to row4 of targetMatrix
        nodeMatrix[ 12:-1 ] = targetMatrix[ 12:-1 ]
        cmds.xform ( node, ws=1, matrix=nodeMatrix )
    elif orient:
        # set row4 x y z to row4 of nodeMatrix
        targetMatrix[ 12:-1 ] = nodeMatrix[ 12:-1 ]
        cmds.xform ( node, ws=1, matrix=targetMatrix )

def messageConnect(fromNode=None, toNode=None, fromName=None, toName=None, category=None):
    '''
    Creates a message attributes on fromNode and toNode with the names fromName and toName respectively
    Connects the two new attributes
    
    '''
    #validation
    if not fromNode or not toNode and (len(cmds.ls(sl=1)) == 2):
        fromNode = cmds.ls(sl=1)[0]
        toNode = cmds.ls(sl=1)[1]
        
    if not fromNode or not toNode:
        return 'Argument Error, messageConnect requires fromNode and toNode as either arguments or 2 selected nodes'
    
    if not fromName or not toName:
        return 'Argument Error, messageConnect requires fromName and toName arguments for newly created attrs'
    
    # Add attributes
    if cmds.attributeQuery(fromName, node = fromNode, exists=1):
        print '%s.%s: Attribute exists' % (fromNode, fromName)
    else:
        cmds.addAttr(fromNode, ln=fromName, at='message', category=category)
        print '%s.%s: Attribute created' % (fromNode, fromName)
        
    if cmds.attributeQuery(toName, node = toNode, exists=1):
        print '%s.%s: Attribute exists' % (toNode, toName)
    else:
        cmds.addAttr(toNode, ln=toName, at='message', category=category)
        print '%s.%s: Attribute created' % (toNode, toName)
        
    # Connect attributes
    cmds.connectAttr('%s.%s' % (fromNode, fromName), '%s.%s' % (toNode, toName), f=1)
    print '%s.%s connected to %s.%s' % (fromNode, fromName, toNode, toName)
    
def parentConnect(parent=None, child=None):
    '''
    Specific method for connecting parent / child relationships in a metarig
    
    '''
    #Validation
    if not parent or not child and (len(cmds.ls(sl=1)) == 2):
        parent = cmds.ls(sl=1)[0]
        child = cmds.ls(sl=1)[1]
        
    if not parent or not child:
        return 'Argument Error, Please supply a parent and child node'
    
    if parent in getAllMetaChildren(child):
        return '%s is a meta descendent of %s and cannot also be its parent' % (parent, child)
    
    # Disconnect from old parent's children array
    oldParent = cmds.listConnections('%s.metaParent' % child)
    
    if type(oldParent) == type([]):
        metaChildren = getMetaChildren(oldParent[0])
        childIndex = metaChildren.index(child)
        cmds.disconnectAttr('%s.message' % child, '%s.metaChildren[%s]' % (oldParent[0], childIndex))
    # Connect to new parent's children array
    metaChildren = getMetaChildren(parent)
    cmds.connectAttr('%s.message' % child, '%s.metaChildren[%s]' % (parent, len(metaChildren)))
    
    # Connect new parent
    messageConnect(fromNode=parent, toNode=child, fromName='message', toName='metaParent')
    
def getMetaChildren(node=None):
    '''
    returns a list of all metaChildren of Node
    
    '''
    if not node and len(cmds.ls(sl=1)) == 1:
        node = cmds.ls(sl=1)
    if not node:
        return 'Please supply a node whose children you wish to list'
    
    metaChildren = cmds.listConnections('%s.metaChildren' % node)
    if not metaChildren:
        metaChildren=[]
        
    return metaChildren

def getAllMetaChildren(node=None):
    '''
    returns a list of all metaDescendents of Node
    
    '''
    if not node and len(cmds.ls(sl=1)) == 1:
        node = cmds.ls(sl=1)
    if not node:
        return 'Please supply a node whose descendents you wish to list'
    
    metaChildren = []
    
    def __getAllMetaChildrenRecurse__(node):
        mc = getMetaChildren(node)
        if mc:
            for n in mc:
                print n
                pass
                __getAllMetaChildrenRecurse__(n)
        metaChildren.append(node)
        
    mc = getMetaChildren(node)
    for n in mc:
        __getAllMetaChildrenRecurse__(n)

    return metaChildren
    
def addDictionaryAttr(node=None, dictName=None):
    '''
    Creates a custom attribute which stores a json encoded dictionary on the specified node
    
    '''
    #Validation
    if not node and (len(cmds.ls(sl=1)) == 1):
        node = cmds.ls(sl=1)[0]
        
    if not node:
        return 'Argument Error, addDictionaryAttr requires node as either argument or a selected node'
    
    if not dictName:
        return 'Argument Error, addDictionaryAttr requires dictName for newly created dictionary'    
        
    # Add attributes
    if cmds.attributeQuery(dictName, node = node, exists=1):
        return 'Argument Error, %s.%s: Dictionary Attribute exists' % (node, dictName)
    else:
        cmds.addAttr(node, ln=dictName, dt="string")
        print '%s.%s: Dictionary Attribute created' % (node, dictName)
        
    # Set initial dictionary value
    cmds.setAttr('%s.%s' % (node, dictName), json.dumps({}),  type="string")
    
def readDict(dict=None):
    '''
    reads a string containing a dictionary and parses it using json 
    
    '''
    return json.loads(dict)

class MetaRig(object):
    '''
    Main meta class
    
    '''
    def __init__(self, name='Rig1', fromNode=None):
        self.name=name
        self.build(fromNode)
        
    def build(self, fromNode):
        if fromNode:
            self.root = fromNode
            self.systems=cmds.listAttr(fromNode, category='metaSystem')
        else:
            self.root = cmds.createNode('network', name=self.name)
            cmds.addAttr(self.root, ln='metaRig', dt="string")
            #messageConnect(fromNode=self.root, toNode=self.root, fromName='message', toName='metaRig')
            self.systems=[]
            
    def addSystem(self, systemType, side, name=None):
        # Adds a new system to the rig for example 'left_arm'.
        # A network node is created as the root for the system and connected via a message attribute to the rig root
        if not name:
            return 'You must provide a unique name for your new system'
        
        if name in self.systems:
            return '%s system already exists. Please provide a unique name for your new system' % name
        
        nw = cmds.createNode('network', name='%s_%s_systemMetaRoot' % (self.name, name))
        messageConnect(fromNode=self.root, toNode=nw, fromName='message', toName='metaRoot', category='metaSystem')
        messageConnect(fromNode=nw, toNode=self.root, fromName='message', toName=name, category='metaSystem')
        
        cmds.addAttr(nw, ln='systemName', dt="string", category='metaSystem')
        cmds.addAttr(nw, ln='systemType', dt="string", category='metaSystem')
        cmds.setAttr('%s.systemName' % nw, name, type="string")
        cmds.setAttr('%s.systemType' % nw, systemType, type="string")
        
        cmds.addAttr(nw, ln='side', at='enum', enumName='centre:left:right', category='metaSystem')
        sideIndex = ['centre', 'left', 'right'].index(side)
        cmds.setAttr('%s.side' % nw, sideIndex)
        
        if not cmds.attributeQuery('metaType', node=nw, exists=1):
            cmds.addAttr(nw, ln='metaType', at='enum', enumName='noSnap:fk:ik', category='metaNode')
        
        self.addUIAttrs(nw)
        
        self.systems.append(name)
    
    def getSystemMetaRoot(self, system):
        # Return the network node at the root of the specified system
        if system in self.systems:
            systemMetaRoot = cmds.listConnections('%s.%s' % (self.root, system))[0]
            return systemMetaRoot
        else:
            return 'System not found: %s' % system
        
    def getMetaRigNodes(self):
        # Returns a list of all nodes connected to the metaRig
        rigNodes = cmds.listConnections('%s.message' % self.root)
        if rigNodes:
            return rigNodes
        else:
            return []
        
    def getSystemNodes(self, system):
        '''
        returns a list of all rignodes in the given system
        '''
        systemMetaRoot = self.getSystemMetaRoot(system)
        systemAttrs = cmds.listAttr(systemMetaRoot, category='metaNode')
        systemNodes = [cmds.listConnections('%s.%s' % (systemMetaRoot, attr))[0] for attr in systemAttrs]
        return systemNodes
    
    def getSystem(self, rigNode):
        '''
        returns the system that the given rigNode belongs to
        '''
        systemMetaRoot = cmds.listConnections('%s.systemMetaRoot'% rigNode)[0]
        system = cmds.getAttr('%s.systemName' % systemMetaRoot)
        return system
        
        
    def getSide(self, rigNode):
        '''
        returns the side of the rigNode (centre, left or right)
        '''
        if cmds.attributeQuery('systemType', node=rigNode, exists=1):
            return cmds.getAttr('%s.side' % rigNode)
        elif cmds.attributeQuery('systemMetaRoot', node=rigNode, exists=1):
            return cmds.getAttr('%s.side' % cmds.listConnections('%s.systemMetaRoot' % rigNode)[0])
        else:
            return 0
        
    def getMetaType(self, rigNode):
        if cmds.attributeQuery('systemType', node=rigNode, exists=1):
            return 0
        else:
            return cmds.getAttr('%s.metaType' % rigNode)
        
    def getSnapNode(self, rigNode):
        if cmds.attributeQuery('snap_target', node=rigNode, exists=1):
            return cmds.listConnections('%s.snap_target' % rigNode)
        else:
            None
            
    
    def addRigNode(self, node=None, system=None, name=None, parent=None):
        # Adds a new rigNode to the specified system for example left_arm>shoulder
        
        #Validation
        if not node:
            if len(cmds.ls(sl=1)) == 1:
                node = cmds.ls(sl=1)[0]
        if not node:
            return 'You must supply a node for your rigNode'
        
        if not system in self.systems:
            return 'System does not exist: %s' % system
        
        systemMetaRoot = self.getSystemMetaRoot(system)
        rigNodeNames = cmds.listAttr(systemMetaRoot, category='metaNode')
        if not rigNodeNames:
            rigNodeNames=[]
        if name in rigNodeNames:
            return '%s rigNode already exists. Please provide a unique name for your new rigNode' % name
        
        rigNodes = self.getMetaRigNodes()
        if node in rigNodes:
            return '%s is already connected to the rig.' % node
        
        messageConnect(fromNode=systemMetaRoot, toNode=node, fromName='message', toName='systemMetaRoot')
        messageConnect(fromNode=self.root, toNode=node, fromName='message', toName='metaRoot')
        messageConnect(fromNode=node, toNode=systemMetaRoot, fromName='message', toName=name, category='metaNode')
        
        # Additional meta attrs
        if not cmds.attributeQuery('metaParent', node=node, exists=1):
            cmds.addAttr(node, ln='metaParent', at='message', category='metaNode')
        if not cmds.attributeQuery('metaChildren', node=node, exists=1):
            cmds.addAttr(node, ln='metaChildren', at='message', multi=1, category='metaNode')
        if not cmds.attributeQuery('metaType', node=node, exists=1):
            cmds.addAttr(node, ln='metaType', at='enum', enumName='noSnap:fk:ik', category='metaNode')
            
        self.addUIAttrs(node)
            
    def addUIAttrs(self, node):
        if not cmds.attributeQuery('buttonPos', node=node, exists=1):
            cmds.addAttr(node, ln='buttonPos', at='short2', category='metaUI')
            cmds.addAttr(node, ln='buttonPosX', p='buttonPos', at='short', category='metaUI')
            cmds.addAttr(node, ln='buttonPosY', p='buttonPos', at='short', category='metaUI')
        if not cmds.attributeQuery('buttonSize', node=node, exists=1):
            cmds.addAttr(node, ln='buttonSize', at='short2', category='metaUI')
            cmds.addAttr(node, ln='buttonSizeX', p='buttonSize', at='short', category='metaUI')
            cmds.addAttr(node, ln='buttonSizeY', p='buttonSize', at='short', category='metaUI')


class PickerGui(QtGui.QWidget):
    '''
    Gui for selecting rig controls and calling functions on them
    '''
    def __init__(self):
        super(PickerGui, self).__init__()
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
        sceneRigs = [node for node in cmds.ls(type='network') if cmds.attributeQuery('metaRig', node=node, exists=1)]
        print 'Metarigs found: %s' % sceneRigs
        return sceneRigs
    
    def getButtonData(self, rigNode):
        '''
        parses button pos, size, colour and tooltip data from rigNode
        returns a dictionary
        
        '''
        buttonPos = [cmds.getAttr('%s.buttonPosX' % rigNode), cmds.getAttr('%s.buttonPosY' % rigNode)]
        buttonSize = [cmds.getAttr('%s.buttonSizeX' % rigNode), cmds.getAttr('%s.buttonSizeY' % rigNode)]
        toolTip = rigNode
        side = self.rig.getSide(rigNode)
        colour = colourList[side]
        metaType = self.rig.getMetaType(rigNode)
                                  
        returnDict = {'pos':buttonPos, 'size':buttonSize, 'toolTip':toolTip, 'colour':colour, 'metaType':metaType}
        
        return returnDict
        
    
    def changeRig(self):
        '''
        Called when a rig is selected from the combobox
        Instantiates a new metaRig to self.rig
        Gathers its metadata and builds the buttons
        
        '''
        self.rig = MetaRig(fromNode=self.sceneRigs[self.sceneRigsComboBox.currentIndex()])
        print self.rig.root
        # Button widget
        try:
            # destroy buttons
            self.buttonWidget.deleteLater()
        except:
            print 'no buttons to delete'
        self.buttonWidget = QtGui.QWidget()
        self.mainLayout.addWidget(self.buttonWidget)
            
        # Build buttons
        rigNodes = self.rig.getMetaRigNodes()
        buttonData = [self.getButtonData(rigNode) for rigNode in rigNodes]
        self.buttonList = []
        for button in buttonData:
            b = QtGui.QPushButton('', parent=self.buttonWidget)
            if button['metaType'] != 0:
                b.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                snap = QtGui.QAction(self)
                snap.setText("snap")
                snap.triggered.connect(self.snap)
                snap.setToolTip(button['toolTip'])
                b.addAction(snap)
                  
            b.setStyleSheet('background-color: rgba(%s, %s, %s, 75);' % (button['colour'][0], button['colour'][1], button['colour'][2]))
            b.setGeometry(button['pos'][0], button['pos'][1], button['size'][0], button['size'][1])
            b.setToolTip(button['toolTip'])
            b.clicked.connect(self.buttonSelect)
            self.buttonList.append(b)
            
        return self.rig
    
    def snap(self):
        rigNode = self.sender().toolTip()
        system = self.rig.getSystem(rigNode)
        systemNodes = self.rig.getSystemNodes(system)
        snapDirection = self.rig.getMetaType(rigNode)
        for node in systemNodes:
            if self.rig.getMetaType(node) == snapDirection:
                snap = self.rig.getSnapNode(node)
                if snap:
                    align(node, snap)
    
    def buttonSelect(self):
        '''
        Called when a gui button is pressed. Selects the rigNode corresponding to the sender button
        Shift+Click behaves as in Maya
        alt click selects all downstream nodes
        ctrl+click selects all nodes in the system
        '''
        sender = self.sender()
        selNodes = []
        modifiers = QtGui.QApplication.keyboardModifiers()
        
        if modifiers == QtCore.Qt.ShiftModifier:
            selNodes = cmds.ls(sl=1)
            if not sender.toolTip() in selNodes:
                selNodes.append(sender.toolTip())
            else:
                selNodes.remove(sender.toolTip())
        elif modifiers == QtCore.Qt.AltModifier:
            selNodes = [sender.toolTip()] + getAllMetaChildren(node=sender.toolTip())
        elif modifiers == QtCore.Qt.ControlModifier:
            system = self.rig.getSystem(sender.toolTip())
            selNodes = self.rig.getSystemNodes(system)
        else:
            selNodes.append(sender.toolTip())
            
        cmds.select(selNodes)
    
    def build(self):
        # get maya main window
        maya = maya_main_window()
        
        # create main window
        self.mainWindow = QtGui.QMainWindow(maya)
        self.mainWindow.setObjectName(self.uiName)
        self.mainWindow.setWindowTitle('Picker GUI')
        self.mainWindow.setMinimumSize(300, 500)
        self.mainWindow.setMaximumSize(300, 500)
        
        # create central widget
        self.centralWidget = QtGui.QWidget()
        self.mainWindow.setCentralWidget(self.centralWidget)
        
        # Main layout
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        
        # ComboBox
        self.sceneRigsComboBox = QtGui.QComboBox()
        self.mainLayout.addWidget(self.sceneRigsComboBox)
        self.sceneRigsComboBox.addItems([rig for rig in self.sceneRigs])
        
            
        # Signals and slots
        self.sceneRigsComboBox.currentIndexChanged.connect(self.changeRig)
        
        self.changeRig()
        
        
        self.mainWindow.show()
        
        
        
        
        

    