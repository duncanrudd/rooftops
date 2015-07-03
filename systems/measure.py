import maya.cmds as cmds
from ROOFTOPS.core import common

def build(start=None, end=None, startLoc=None, endLoc=None, name=''):
    '''
    Creates a distance tool with locators aligned to start and end nodes
    Returns a dictionary containing keys for shape, transform, startLoc and endLoc
    
    If locators are supplied for either startLoc or endLoc, they are used in place of creating new ones
    
    '''
    
    if not start or not end:
        return common.showDialog('Agument Error. Please supply start and end nodes')
        
    distanceShape = cmds.createNode('distanceDimShape')
    distanceTransform = cmds.listRelatives(distanceShape, parent=True, fullPath=True)
    
    if not startLoc:
        startLoc = cmds.spaceLocator(name = '%s_distance_start_loc' % name)[0]
        common.align(startLoc, start)
    
    if not endLoc:
        endLoc = cmds.spaceLocator(name = '%s_distance_end_loc' % name)[0]
        common.align(endLoc, end)
    
    cmds.connectAttr('%s.worldPosition[0]' % startLoc, '%s.startPoint' % distanceShape)
    cmds.connectAttr('%s.worldPosition[0]' % endLoc, '%s.endPoint' % distanceShape)
    
    distanceTransform = cmds.rename(distanceTransform, name, ignoreShape=True)
    distanceShape = cmds.rename(distanceShape, '%sShape' % distanceTransform)
    
    returnDict = {'shape':distanceShape, 'xform':distanceTransform, 'start':startLoc, 'end':endLoc}
    return returnDict