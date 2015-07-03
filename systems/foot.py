import maya.cmds as cmds

from rooftops.core import common

def build( targ=None, mesh=None, paramU=None, paramV=None, name='' ):
    '''
    creates a follicle at the closest point to targ on the surface of mesh
    
    '''
    if paramU == None or paramV == None:
        print paramU
        print paramV
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
    #constGrp = cmds.group(empty=1, name=(name+'_const_grp'))
    #common.align(constGrp, follXform, translate=False )
    #common.align(constGrp, targ, orient=False )
    #cmds.parent(constGrp, follXform)
    
    if paramU == None or paramV == None:
        cmds.delete( pmm1 )
        cmds.delete( closestPoint )
    
    return follXform

def buildFoot(name='', numJoints=5, side='rt'):
    # Create nurbsPlanes
    ikPlane = cmds.nurbsPlane(u=4, v=8, name=(name+'_ikPlane'), axis=[0,1,0])[0]
    fkPlane = cmds.nurbsPlane(u=4, v=8, name=(name+'_fkPlane'), axis=[0,1,0])[0]
    
    # Create follicles
    ikFollicles=[]
    for i in range(numJoints):
        f = build(mesh=ikPlane, paramV=(1.0/(numJoints-1) * i), paramU=0.5, name=(name + '_ik_' + str(i)))
        ikFollicles.append(f)
        
    fkFollicles=[]
    for i in range(numJoints):
        f = build(mesh=fkPlane, paramV=(1.0/(numJoints-1) * i), paramU=0.5, name=(name + '_fk_' + str(i)))
        fkFollicles.append(f)
        
    # Create IK Control
    ikCtrl = cmds.circle(name=(name + '_ik_bend_ctrl'))[0]
    common.insertGroup(ikCtrl)
    cmds.addAttr(ikCtrl, ln='falloff', at='double', keyable=1, minValue=0.01)
        
    # Create deformers
    ikBend1 = cmds.nonLinear(ikPlane, type='bend')
    ikBend1_bend = cmds.rename(ikBend1[0], name+'_ikBend_1')
    ikBend1_handle = cmds.rename(ikBend1[1], name+'_ikBend_1_handle')
    common.insertGroup(ikBend1_handle)
    cmds.xform(ikBend1_handle, ws=0, rotation=(90, 0, 90))
    
    uc = cmds.createNode('unitConversion', name=(name + '_ikBend_1_falloff_uc'))
    cmds.connectAttr(ikCtrl+'.falloff', uc+'.input')
    cmds.setAttr(uc+'.conversionFactor', -1.0)
    
    md = cmds.createNode('multiplyDivide', name=(name+'_ikBend_1_curvature_md'))
    cmds.setAttr(md+'.operation', 2)
    cmds.connectAttr(ikCtrl+'.rx', md+'.input1X')
    cmds.connectAttr(ikCtrl+'.falloff', md+'.input2X')
    
    cmds.connectAttr(md+'.outputX', ikBend1_bend+'.curvature')
    cmds.connectAttr(uc+'.output', ikBend1_bend+'.lowBound')
    cmds.setAttr(ikBend1_bend+'.highBound', 0.0)
    cmds.connectAttr(ikCtrl+'.tx', ikBend1_handle+'.tx')
    cmds.connectAttr(ikCtrl+'.tz', ikBend1_handle+'.tz')
    cmds.connectAttr(ikCtrl+'.ry', ikBend1_handle+'.ry')
    
    # Create FK Control
    fkCtrl = cmds.circle(name=(name + '_fk_bend_ctrl'))[0]
    common.insertGroup(fkCtrl)
    cmds.addAttr(fkCtrl, ln='falloff', at='double', keyable=1, minValue=0.01)
        
    # Create fk deformers
    fkBend1 = cmds.nonLinear(fkPlane, type='bend')
    fkBend1_bend = cmds.rename(fkBend1[0], name+'_fkBend_1')
    fkBend1_handle = cmds.rename(fkBend1[1], name+'_fkBend_1_handle')
    common.insertGroup(fkBend1_handle)
    cmds.xform(fkBend1_handle, ws=0, rotation=(90, 0, 90))
    
    uc = cmds.createNode('unitConversion', name=(name + '_fkBend_1_curvature_uc'))
    cmds.connectAttr(fkCtrl+'.rx', uc+'.input')
    cmds.setAttr(uc+'.conversionFactor', -57.296)
    
    md = cmds.createNode('multiplyDivide', name=(name+'_fkBend_1_curvature_md'))
    cmds.setAttr(md+'.operation', 2)
    cmds.connectAttr(uc+'.output', md+'.input1X')
    cmds.connectAttr(fkCtrl+'.falloff', md+'.input2X')
    
    cmds.connectAttr(md+'.outputX', fkBend1_bend+'.curvature')
    cmds.connectAttr(fkCtrl+'.falloff', fkBend1_bend+'.highBound')
    cmds.setAttr(fkBend1_bend+'.lowBound', 0.0)
    cmds.connectAttr(fkCtrl+'.tx', fkBend1_handle+'.tx')
    cmds.connectAttr(fkCtrl+'.tz', fkBend1_handle+'.tz')
    cmds.connectAttr(fkCtrl+'.ry', fkBend1_handle+'.ry')
        
#buildFoot()