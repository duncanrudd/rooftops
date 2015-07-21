import maya.cmds as cmds

from rooftops.core import common
from rooftops.systems import rivet, controls

def buildFoot(name='', numJoints=5, side='rt', blendAttr=None, cleanup=1):
    
    # main ik group
    grp = cmds.group(empty=1, name=(name+'_ik_grp'))
    noTouch_grp = cmds.group(empty=1, name=(name+'_ik_noTouch_grp'))
    cmds.parent(noTouch_grp, grp)
    
    # Create ik nurbsPlane
    ikPlane = cmds.nurbsPlane(u=7, v=7, name=(name+'_ikPlane'), axis=[0,1,0])[0]
    cmds.parent(ikPlane, noTouch_grp)
    
    # Create ik follicles
    ikFollicles=[]
    for i in range(numJoints):
        f = rivet.build(mesh=ikPlane, paramV=(1.0/(numJoints-1) * i), paramU=0.5, name=(name + '_ik_' + str(i+1)))
        ikFollicles.append(f)
        cmds.parent(f, noTouch_grp)
        
    # Create IK Control
    ##ikCtrl = cmds.circle(name=(name + '_ik_bend_ctrl'))[0]
    ikCtrl = controls.circleBumpCtrl(radius=5.0, name=(name + '_ik_bend_ctrl'), axis='x')[0]
    cmds.parent(ikCtrl, grp)
    common.insertGroup(ikCtrl)
    cmds.addAttr(ikCtrl, ln='falloff', at='double', keyable=1, minValue=0.01)
        
    # Create deformers
    ikBend1 = cmds.nonLinear(ikPlane, type='bend')
    ikBend1_bend = cmds.rename(ikBend1[0], name+'_ikBend_1')
    ikBend1_handle = cmds.rename(ikBend1[1], name+'_ikBend_1_handle')
    handle_grp = common.insertGroup(ikBend1_handle)
    driven_grp = common.insertGroup(ikBend1_handle, 'driven')
    cmds.xform(ikBend1_handle, ws=0, rotation=(90, 0, 90))
    cmds.parent(handle_grp, noTouch_grp)
    
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
    cmds.connectAttr(ikCtrl+'.tx', driven_grp+'.tx')
    cmds.connectAttr(ikCtrl+'.tz', driven_grp+'.tz')
    cmds.connectAttr(ikCtrl+'.ry', driven_grp+'.ry')
    
    # Create IK toe Control
    ##ikToeCtrl = cmds.circle(name=(name + '_ik_toe_ctrl'))[0]
    ikToeCtrl = controls.circleBumpCtrl(radius=3.0, name=(name + '_ik_toe_ctrl'), axis='x')[0]
    cmds.parent(ikToeCtrl, ikCtrl)
    common.insertGroup(ikToeCtrl)
        
    # Create deformers
    ikToeBend1 = cmds.nonLinear(ikPlane, type='bend')
    ikToeBend1_bend = cmds.rename(ikToeBend1[0], name+'_ikToeBend_1')
    ikToeBend1_handle = cmds.rename(ikToeBend1[1], name+'_ikToeBend_1_handle')
    cmds.parent(ikToeBend1_handle, driven_grp)
    cmds.xform(ikToeBend1_handle, ws=0, rotation=(90, 0, 90))
    
    uc = cmds.createNode('unitConversion', name=(name + '_ikToeBend_1_curvature_uc'))
    cmds.connectAttr(ikToeCtrl+'.rx', uc+'.input')
    cmds.setAttr(uc+'.conversionFactor', -57.296)
    
    md = cmds.createNode('multiplyDivide', name=(name+'_ikToeBend_1_curvature_md'))
    cmds.setAttr(md+'.operation', 2)
    cmds.connectAttr(uc+'.output', md+'.input1X')
    cmds.connectAttr(ikCtrl+'.falloff', md+'.input2X')
    
    cmds.connectAttr(md+'.outputX', ikToeBend1_bend+'.curvature')
    cmds.connectAttr(ikCtrl+'.falloff', ikToeBend1_bend+'.highBound')
    cmds.setAttr(ikToeBend1_bend+'.lowBound', 0.0)
    
    # main fk group
    fk_grp = cmds.group(empty=1, name=(name+'_fk_grp'))
    fk_noTouch_grp = cmds.group(empty=1, name=(name+'_fk_noTouch_grp'))
    cmds.parent(fk_noTouch_grp, fk_grp)
    
    # fk nurbsPlane
    fkPlane = cmds.nurbsPlane(u=7, v=7, name=(name+'_fkPlane'), axis=[0,1,0])[0]
    cmds.parent(fkPlane, fk_noTouch_grp)
    
    # Create fk follicles
    fkFollicles=[]
    for i in range(numJoints):
        f = rivet.build(mesh=fkPlane, paramV=(1.0/(numJoints-1) * i), paramU=0.5, name=(name + '_fk_' + str(i+1)))
        fkFollicles.append(f)
        cmds.parent(f, fk_noTouch_grp)
    
    # Create FK Control
    ##fkCtrl = cmds.circle(name=(name + '_fk_bend_ctrl'))[0]
    fkCtrl = controls.circleBumpCtrl(radius=4.0, name=(name + '_fk_bend_ctrl'), axis='x')[0]
    cmds.parent(fkCtrl, fk_grp)
    common.insertGroup(fkCtrl)
    cmds.addAttr(fkCtrl, ln='falloff', at='double', keyable=1, minValue=0.01)
        
    # Create fk deformers
    fkBend1 = cmds.nonLinear(fkPlane, type='bend')
    fkBend1_bend = cmds.rename(fkBend1[0], name+'_fkBend_1')
    fkBend1_handle = cmds.rename(fkBend1[1], name+'_fkBend_1_handle')
    handle_grp = common.insertGroup(fkBend1_handle)
    driven_grp = common.insertGroup(fkBend1_handle, 'driven')
    cmds.xform(fkBend1_handle, ws=0, rotation=(90, 0, 90))
    cmds.parent(handle_grp, fk_noTouch_grp)
    
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
    cmds.connectAttr(fkCtrl+'.tx', driven_grp+'.tx')
    cmds.connectAttr(fkCtrl+'.tz', driven_grp+'.tz')
    cmds.connectAttr(fkCtrl+'.ry', driven_grp+'.ry')
    
    # Set up blending attribute
    ikAttr=None
    fkAttr=None
    if not blendAttr:
        cmds.addAttr(grp, longName='state', at='enum', enumName='ik:fk', keyable=True )
        stateRev = cmds.createNode('reverse', name=(name+'_state_rev'))
        cmds.connectAttr(grp+'.state', stateRev+'.inputX')
        fkAttr=(grp+'.state')
        ikAttr=(stateRev+'.outputX')
    else:
        fkAttr=blendAttr
        # Check whether a reverse node is connected to blendAttr
        revCheck = cmds.listConnections(fkAttr, type='reverse')
        if revCheck:
            ikAttr = revCheck[0]+'.outputX'
        else:
            stateRev = cmds.createNode('reverse', name=(name+'_state_rev'))
            cmds.connectAttr(fkAttr, stateRev+'.inputX') 
            ikAttr=(stateRev+'.outputX')
    
    joints_grp = cmds.group(empty=1, name=(name+'_joints_grp'))
    cmds.parent(joints_grp, grp)
    
    # Build joints
    for i in range(numJoints):
        cmds.select(joints_grp)
        pos = cmds.xform(ikFollicles[i], q=1, t=1, ws=1)
        j = cmds.joint(name=(name+'_'+str(i+1)+'_jnt'), p=pos)
        #Constrain between follicles
        pc = cmds.parentConstraint([ikFollicles[i], fkFollicles[i]], j)[0]
        weightAliasList = [str(w) for w in cmds.parentConstraint(j, q=1, weightAliasList=1)]
        cmds.connectAttr(ikAttr, pc+'.'+weightAliasList[0])
        cmds.connectAttr(fkAttr, pc+'.'+weightAliasList[1])
        
    if cleanup:
        common.attrCtrl(lock=True, keyable=False, channelBox=False, nodeList=[ikCtrl, fkCtrl], attrList=['ty', 'rz', 'sx', 'sy', 'sz', 'visibility'])
        common.attrCtrl(lock=True, keyable=False, channelBox=False, nodeList=[ikToeCtrl], attrList=['tx', 'ty', 'tz', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility'])
        
        

        
#buildFoot()