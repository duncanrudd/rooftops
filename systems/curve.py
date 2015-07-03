import maya.cmds as cmds
from ROOFTOPS.core import common

def curveBetweenNodes(start=None, end=None, name=''):
    '''
    Makes a degree 3 nurbs curve with 4 cvs between two nodes
    
    '''
    # Validation of args
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
        return common.showDialog( 'Argument Error', 'Cannot determine start and end points' )
    
    points = common.pointsAlongVector(start=startPos, end=endPos, divisions=3)
    
    # create the curve
    crv = cmds.curve(p=points, k=[0,0,0,1,1,1], name='%s_crv' % name)
    return crv


######################################################################################################################################################


def nodesAlongCurve(crv=None, numNodes=6, name='', followAxis='x', upAxis='y', upNode=None):
    '''
    creates a motionPath node for each in numNodes and connects its parameter to the supplied curve
    attaches an empty group to each motionpath node
    returns a dictionary with keys for the motionPath nodes and the groups along the curve as well as the rootGrp
    
    '''
    # Validation of args
    if not crv:
        if len(cmds.ls(sl=1)) == 1:
            crv = cmds.ls(sl=1)[0]
        else:
            return common.showDialog( 'Argument Error', 'Please supply or select a nurbs curve' )
        
    upDict = {'x':(1.0, 0.0, 0.0), 'y':(0.0, 1.0, 0.0), 'z':(0.0, 0.0, 1.0)}
    
    #rootGrp = cmds.group(empty=1, name='%s_pathNodes_grp' % name)
    #cmds.setAttr('%s.inheritsTransform' % rootGrp, 0)
    
    returnDict={'mpNodes':[], 'grps':[]}
       
    for i in range( numNodes ):
        n = cmds.group(empty=1, name='%s_%s_grp' % (name, i+1))
        #cmds.parent(n, rootGrp)
        mp = cmds.pathAnimation(n, fm=1, f=1, fa=followAxis, ua=upAxis, wu=upDict[upAxis], curve=crv, name='%s_%s_mp' % (name, i+1))
        if upNode:
            cmds.pathAnimation(mp, e=1, wut='objectrotation', wuo=upNode)
        
        # Delete all the crap that comes with the motion path node
        mpAnim = cmds.listConnections( '%s.uValue' % mp, d=False, s=True, type='animCurve' )
        adlX = cmds.listConnections( '%s.xCoordinate' % mp, d=True, s=False, type='addDoubleLinear' )
        cmds.delete(adlX)
        adlY = cmds.listConnections( '%s.yCoordinate' % mp, d=True, s=False, type='addDoubleLinear' )
        cmds.delete(adlY)
        adlZ = cmds.listConnections( '%s.zCoordinate' % mp, d=True, s=False, type='addDoubleLinear' )
        cmds.delete(adlZ)
        cmds.delete(mpAnim)
        
        # Manually connect up the position
        cmds.connectAttr('%s.xCoordinate' % mp, '%s.tx' % n, f=1)
        cmds.connectAttr('%s.yCoordinate' % mp, '%s.ty' % n, f=1)
        cmds.connectAttr('%s.zCoordinate' % mp, '%s.tz' % n, f=1)
        
        cmds.setAttr('%s.uValue' % mp, (1.0 / (numNodes-1))*i)
        
        returnDict['mpNodes'].append(mp)
        returnDict['grps'].append(n)
        
    return returnDict
        
        
######################################################################################################################################################

def bindCurve(crv=None):
    '''
    Creates a joint for each cv in the supplied or selected curve
    performs a smooth bind on the curve to the joints
    returns a list of the newly created joints
    
    '''
    # Validation of args
    if not crv:
        if len(cmds.ls(sl=1)) == 1:
            crv = cmds.ls(sl=1)[0]
        else:
            return common.showDialog( 'Argument Error', 'Please supply or select a nurbs curve' )
        
    jointList = []
        
    cvs = cmds.getAttr("%s.cv[*]" % crv)
    
    for cv in range(len(cvs)):
        cmds.select(clear=1)
        j = cmds.joint(p=cvs[cv], name='%s_%s_jnt' %(crv, cv+1))
        jointList.append(j)
        
    cmds.skinCluster(jointList, crv, tsb=1, name='%s_skinCluster' % crv)
    
    return jointList
        
        
    