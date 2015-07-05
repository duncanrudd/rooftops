# Module for generic centralised functions such as naming of objects / colour coding of controls etc...
# Imports
import maya.cmds as cmds
import maya.OpenMaya as om
import os, math


# Functions
def colorize( color=None, nodeList=[] ):
    '''
    takes a node ( or list or nodes ) and enables the drawing overrides.
    'Color' specifies either an integer for the required color or a string corresponding to a key in colorDict
    if nodelist is not supplied, will attempt to work on selected nodes.
    
    '''
    if not color:
        raise RuntimeError, 'color not specified. You must supply either a string or integer.'
    
    colorDict = {
                   'center':14, # green
                   'right':13, # red
                   'left':6, # blue
                   'red':13,
                   'blue':6,
                   'yellow':17,
                   'green':14,
                   'purple':9,
                   'cn':14, # green
                   'rt':13, # red
                   'lf':6, # blue
                  }
    
    if type( color ) == type( 'hello' ) or type( color ) == type( u'hello' ):
        color = colorDict[ color ]
    
    if not nodeList:
        nodeList = cmds.ls( sl=True )
    else:
        if type( nodeList ) == type( 'hello' ) or type( nodeList ) == type( u'hello' ):
            nodeList = [ nodeList ]
            
    for n in nodeList:
        cmds.setAttr('%s.overrideEnabled' % n, 1)
        cmds.setAttr('%s.overrideColor' % n, color)
        
        
######################################################################################################################################################


def getCharDir( char ):
    '''
    returns the directory path to the supplied character
    '''
    return os.path.join( os.path.dirname( __file__ ), '..', 'characters', char)


######################################################################################################################################################

def pointsAlongVector( start='', end='', divisions=2 ):
    '''
    returns a list of points that lie on a line between start and end
    'divisions' specifies the number of points to return.
    divisions = 2 (default) will return the start and end points with one intermediate point: [ p1(start), p2, p3(end) ]
    
    start and end can be supplied as lists, tuples or nodes. If they are not supplied, and 2 scene nodes are selected
    will attempt to use their world space positions as start and end
        
    creates a vector by subtracting end from start
    stores length of vector
    normalizes vector
    multiplies normalized vector by length / divisions
    
    '''
    startPos, endPos = None, None
    if not start or not end and len( cmds.ls( sl=True ) ) == 2:
        startPos = cmds.xform( cmds.ls( sl=True )[0], translation=True, query=True, ws=True )
        endPos = cmds.xform( cmds.ls( sl=True )[1], translation=True, query=True, ws=True )
    else:
        if type( start ) == type( 'hello' ) or type( start ) == type( u'hello' ):
            startPos = cmds.xform( str(start), translation=True, query=True, ws=True )
        else:
            startPos = start
            
        if type( end ) == type( 'hello' ) or type( end ) == type( u'hello' ):    
            endPos = cmds.xform( str(end), translation=True, query=True, ws=True )
        else:
            endPos = end

    if not startPos or not endPos:
        return showDialog( 'Argument Error', 'Cannot determine start and end points' )
        
    startVec = om.MVector(startPos[0], startPos[1], startPos[2])
    endVec = om.MVector(endPos[0], endPos[1], endPos[2])
    newVec = endVec - startVec
    segLength = newVec.length() / divisions
    newVec.normalize()
    
    points = []
    
    points.append(tuple(startPos))

    for p in range( 1, divisions ):
        point = newVec * segLength * p + startVec
        points.append((point.x, point.y, point.z))
        
    points.append(tuple(endPos))
    
    return points

######################################################################################################################################################

def insertGroup( node=None, suffix='grp' ):
    '''
    creates an empty group aligned to the selected node and inserts it into the hierarchy;
    
    '''
    if not node:
        node = cmds.ls(sl=1)[0]
    if node:
        parent = cmds.listRelatives(node, p=1)
        grp = cmds.group(empty=1, n='%s_%s' % (node, suffix))
        align(node=grp, target=node)
        if parent:
            cmds.parent(grp, parent)
            
        cmds.parent(node, grp)
        
        return grp
    else:
        return showDialog( 'Argument Error', 'Cannot determine the node you wish to group' )
    
    
######################################################################################################################################################

def align( node=None, target=None, translate=True, orient=True, scale=False ):
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
            return showDialog( 'Argument Error', 'Cannot determine nodes to align' )

    targetMatrix = cmds.xform( target, q=True, ws=1, matrix=True )
    nodeMatrix = cmds.xform( node, q=True, ws=1, matrix=True )
    
    nodeScale = cmds.getAttr(node+'.scale')[0]
    
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
        
    if not scale:
        cmds.setAttr(node+'.scale', nodeScale[0], nodeScale[1], nodeScale[2])
        
######################################################################################################################################################
        
def attrCtrl(lock=True, keyable=False, channelBox=False, nodeList=[], attrList=[]):
    '''
    Takes a list of nodes and sets locks/unlocks shows/hides attributes in attrList
    
    '''
    if nodeList:
        for node in nodeList:
            if attrList:
                for attr in attrList:
                    if cmds.attributeQuery(attr, node=node, exists=True):
                        cmds.setAttr('%s.%s' % (node, attr), lock=lock, keyable=keyable, channelBox=channelBox)
            else:
                return showDialog( 'Argument Error', 'No nodes supplied for attribute control' )
    else:
        return showDialog( 'Argument Error', 'No nodes supplied for attribute control' )
    

######################################################################################################################################################

def getDistance( object1, object2 ):
    '''
    Calculates distance between two Transforms using magnitude
    '''
    def mag(numbers):
        num = 0
        for eachNumber in numbers:
            num += pow(eachNumber, 2)
            
        mag = math.sqrt(num)
        return mag

    vector1 = (cmds.xform(object1, query=1, worldSpace=1, translation=1))
    vector2 = (cmds.xform(object2, query=1, worldSpace=1, translation=1))
    
    calc = []
    calc.append(vector1[0] - vector2[0])
    calc.append(vector1[1] - vector2[1])
    calc.append(vector1[2] - vector2[2])
    
    return mag(calc)

######################################################################################################################################################

def showDialog( title, message, button=[] ):
    '''
    Shows an error dialog for the user.
    Supply two strings, a title and a message. The message accepts '\n' to break lines.
    If a list of buttons is supplied, the function returns the user input.
    '''
    ret = cmds.confirmDialog( title=title, message=message, button=button )
    if button != []:
        return ret

######################################################################################################################################################    
    
def blendAttrs(targ1=None, targ2=None, driven=None, blendAttr=None, translate=1, rotate=1):
    '''
    sets up blending of translation / rotation values from targs 1 & 2 on the driven node.
    If a blendAttr is supplied, this is connected to the blender value
    
    '''
    if not targ1 and not targ2 and not driven:
        if len(cmds.ls(sl=1)) == 3:
            targ1 = cmds.ls(sl=1)[0]
            targ2 = cmds.ls(sl=1)[1]
            driven = cmds.ls(sl=1)[2]
        else:
            return showDialog( 'Argument Error', 'Please supply or select targ1, targ2 and driven nodes' )
    
    if translate:
        t_bc = cmds.createNode('blendColors', name='%s_translate_bc' % driven)
        cmds.connectAttr('%s.t' % targ2, '%s.color1' % t_bc)
        cmds.connectAttr('%s.t' % targ1, '%s.color2' % t_bc)
        if blendAttr:
            cmds.connectAttr(blendAttr, '%s.blender' % t_bc)
        cmds.connectAttr('%s.output' % t_bc, '%s.t' % driven)
            
    if rotate:
        r_bc = cmds.createNode('blendColors', name='%s_rotate_bc' % driven)
        cmds.connectAttr('%s.rotate' % targ2, '%s.color1' % r_bc)
        cmds.connectAttr('%s.rotate' % targ1, '%s.color2' % r_bc)
        if blendAttr:
            cmds.connectAttr(blendAttr, '%s.blender' % r_bc)
        cmds.connectAttr('%s.output' % r_bc, '%s.rotate' % driven)


###################################################################################################################################################### 

def getShape(transform=None):
    '''
    returns the first shape of the specified transform
    
    '''
    shape = cmds.listRelatives( transform, children=1, shapes=1 )[ 0 ]
    return shape

######################################################################################################################################################

def placePoleVector(node1=None, node2=None, node3=None, axis='-z', mult=30):
    '''
    Uses vector calculations to determine the placement of the pole vector on the plane formed by the three nodes supplied.
    If the three nodes are in line, takes the middle point and displaces it along the axis specified
    Returns a tuple
    
    '''
    # Validation
    if not node1 or not node2 or not node3 and len( cmds.ls( sl=True ) ) == 3:
        node1 = cmds.ls( sl=True )[0]
        node2 = cmds.ls( sl=True )[1]
        node3 = cmds.ls( sl=True )[2]
        p1 = cmds.xform( node1, translation=True, query=True, ws=True )
        p2 = cmds.xform( node2, translation=True, query=True, ws=True )
        p3 = cmds.xform( node3, translation=True, query=True, ws=True )
    else:
        if type( node1 ) == type( 'hello' ) or type( node1 ) == type( u'hello' ):
            p1 = cmds.xform( str(node1), translation=True, query=True, ws=True )
            
        if type( node2 ) == type( 'hello' ) or type( node2 ) == type( u'hello' ):
            p2 = cmds.xform( str(node2), translation=True, query=True, ws=True )
            
        if type( node3 ) == type( 'hello' ) or type( node3 ) == type( u'hello' ):
            p3 = cmds.xform( str(node3), translation=True, query=True, ws=True )

    if not p1 or not p2 or not p3:
        return showDialog( 'Argument Error', 'Cannot determine p1, p2 and p3' )
    
    # check to see whether the points are in line
    v1 = om.MVector(p1[0], p1[1], p1[2])
    v2 = om.MVector(p2[0], p2[1], p2[2])
    v3 = om.MVector(p3[0], p3[1], p3[2])
    v4 = v2 - v1
    v5 = v3 - v1
    
    if v4.angle(v5) < 0.00001 or v4.angle(v5) > 3.1415:
        # Create a matrix from p2
        p2Matrix = cmds.xform( node2, q=True, matrix=True, ws=True )
        returnMatrix = om.MMatrix()
        om.MScriptUtil.createMatrixFromList( p2Matrix, returnMatrix)
        
        row = {'x':0, '-x':0, 'y':1, '-y':1, 'z':2, '-z':2}[axis]
        mult = mult * {'x':1, '-x':-1, 'y':1, '-y':-1, 'z':1, '-z':-1}[axis]
        
        rowVec = om.MVector(returnMatrix( row, 0 ), returnMatrix( row, 1 ), returnMatrix( row, 2 ))
        resultVec = (rowVec * mult) + v2
        return (resultVec.x, resultVec.y, resultVec.z)
    else:
        midPoint = pointsAlongVector( start=p1, end=p3, divisions=2 )[ 1 ]
        v6 = om.MVector(midPoint[0], midPoint[1], midPoint[2])
        resultVec = ( (v2 - v6) * mult ) + v6
        return (resultVec.x, resultVec.y, resultVec.z)
    
    
    



