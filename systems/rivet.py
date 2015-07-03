import maya.cmds as cmds
from ROOFTOPS.core import common

def build( targ=None, mesh=None, name='' ):
    '''
    creates a follicle at the closest point to targ on the surface of mesh
    
    '''
    if not targ or not mesh:
        return 'Argument Error, Please provide nodes for targ and mesh arguments'
    
    if cmds.nodeType(mesh) == 'transform':
        mesh = cmds.listRelatives(mesh, s=1)[0]
    
    targPos = cmds.xform( targ, q=1, ws=1, t=1 )
    pmm1 = cmds.createNode('pointMatrixMult')
    cmds.setAttr('%s.inPoint' % pmm1, targPos[0], targPos[1], targPos[2] )
    cmds.connectAttr('%s.worldInverseMatrix[0]' % mesh, '%s.inMatrix' % pmm1)
    targPos = cmds.getAttr('%s.output' % pmm1)[0]
    print targPos

    closestPoint=''
    
    if cmds.nodeType(mesh) == 'mesh':
        closestPoint = cmds.createNode('closestPointOnMesh')
        cmds.setAttr( '%s.inPosition' % closestPoint, targPos[0], targPos[1], targPos[2] )
        cmds.connectAttr( '%s.worldMesh[0]' % mesh, '%s.inMesh' % closestPoint )
    else:
        closestPoint = cmds.createNode('closestPointOnSurface')
        cmds.setAttr( '%s.inPosition' % closestPoint, targPos[0], targPos[1], targPos[2] )
        cmds.connectAttr( '%s.worldSpace[0]' % mesh, '%s.inputSurface' % closestPoint )
    
    paramU = cmds.getAttr( '%s.result.parameterU' % closestPoint )
    paramV = cmds.getAttr( '%s.result.parameterV' % closestPoint )
    
    # Create follicle
    foll = cmds.createNode('follicle')
    follXform = cmds.listRelatives(foll, p=1)[0]
    follXform = cmds.rename(follXform, (name+'_foll'))
    follShape = cmds.listRelatives(follXform, c=1)[0]
    
    if cmds.nodeType(mesh) == 'mesh':
        cmds.connectAttr( '%s.outMesh' % mesh, '%s.inputMesh' % follShape )
    else:
        cmds.connectAttr( '%s.local' % mesh, '%s.inputSurface' % follShape)
    cmds.connectAttr( '%s.worldMatrix[0]' % mesh, '%s.inputWorldMatrix' % follShape )
    
    cmds.connectAttr( '%s.outRotate' % follShape, '%s.r' % follXform )
    cmds.connectAttr( '%s.outTranslate' % follShape, '%s.t' % follXform )
    
    cmds.setAttr( '%s.parameterU' % follShape, paramU )
    cmds.setAttr( '%s.parameterV' % follShape, paramV )
    
    cmds.setAttr( '%s.inheritsTransform' % follXform, 0 )
    
    # Create group at exact location of targ - this is the node to constrain to
    constGrp = cmds.group(empty=1, name=(name+'_const_grp'))
    common.align(constGrp, follXform, translate=False )
    common.align(constGrp, targ, orient=False )
    cmds.parent(constGrp, follXform)
    
    cmds.delete( pmm1 )
    cmds.delete( closestPoint )
    
    return {'follicle':follXform, 'constGrp':constGrp}
    
#build( targ='locator1', mesh='pPlane1', name='test' )