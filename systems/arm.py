import maya.cmds as cmds
import math
from rooftops.core import common

def build(upArm=None, lowArm=None, wrist=None, end=None, side='lf', twistJoints=5, globalScaleAttr=None, cleanup=0):
    '''
    makes a triple chain arm using a set of 4 existing hierarchical joints
    
    '''
    #Validation
    if not upArm or not lowArm or not wrist or not end:
        if len(cmds.ls(sl=1)) == 4:
            upArm = cmds.ls(sl=1)[0]
            lowArm = cmds.ls(sl=1)[1]
            wrist = cmds.ls(sl=1)[2]
            end = cmds.ls(sl=1)[3]
        else:
            return common.showDialog( 'Argument Error', 'Please supply 4 hierarchical joints' )
    
    # Root group
    root = cmds.group(empty=1, name='%s_arm_grp' % side)
    
    #Constrain group which is aligned to the first joint and can be used to attach the arm to a shoulder
    const = cmds.group(empty=1, name='%s_arm_const_grp' % side)
    common.align(const, upArm)
    cmds.parent(const, root)
    
    # result chainw
    dupes = cmds.duplicate(upArm, rc=1)
    resultChain = []
    for i in range(4):
        jnt = cmds.rename(dupes[i], '%s_%s_result_jnt' %(side, ['upArm', 'lowArm', 'wrist', 'end'][i]) )
        resultChain.append(jnt)
        
    cmds.parent(resultChain[0], const)
    
    # fk chain
    dupes = cmds.duplicate(resultChain[0], rc=1)
    fkChain = []
    for i in range(4):
        jnt = cmds.rename(dupes[i], '%s_%s_fk_jnt' %(side, ['upArm', 'lowArm', 'wrist', 'end'][i]) )
        fkChain.append(jnt)
        
    
    # ik chain
    dupes = cmds.duplicate(resultChain[0], rc=1)
    ikChain = []
    for i in range(4):
        jnt = cmds.rename(dupes[i], '%s_%s_ik_jnt' %(side, ['upArm', 'lowArm', 'wrist', 'end'][i]) )
        ikChain.append(jnt)
        
    # Settings ctrl
    settingsCtrl = controls.crossCtrl(name='%s_arm_settings_ctrl' % side)
    settingsShape = common.getShape(settingsCtrl)
    common.align(settingsCtrl, const)
    cmds.parent(settingsCtrl, root)
    # ik / fk attr
    cmds.addAttr( settingsCtrl, longName='state', at='enum', enumName='ik:fk', keyable=True )
    stateRev = cmds.createNode('reverse', name='%s_arm_state_rev' % side)
    cmds.connectAttr('%s.state' % settingsCtrl, '%s.inputX' % stateRev)
    # bendy ctrls switch
    cmds.addAttr( settingsCtrl, longName='bendy_ctrls', at='enum', enumName='hide:show', keyable=True )
    
    ##################################################################################################################################### FK Ctrls
    fkGrp = cmds.group(empty=1, name='%s_arm_fk_grp' % side)
    cmds.parent(fkGrp, root)
    cmds.connectAttr('%s.state' % settingsCtrl, '%s.visibility' % fkGrp)
    
    # fk up arm
    fkUpArmCtrl = controls.circleBumpCtrl(name='%s_upArm_fk_ctrl' % side, axis='x', radius=10)[0]
    common.align(fkUpArmCtrl, fkChain[0])
    cmds.parent(fkUpArmCtrl, fkGrp)
    common.insertGroup(fkUpArmCtrl)
    
    # fk low arm
    fkLowArmCtrl = controls.circleBumpCtrl(name='%s_lowArm_fk_ctrl' % side, axis='x', radius=10)[0]
    common.align(fkLowArmCtrl, fkChain[1])
    cmds.parent(fkLowArmCtrl, fkUpArmCtrl)
    
    # fk hand
    fkHandCtrl = controls.circleBumpCtrl(name='%s_hand_fk_ctrl' % side, axis='x', radius=10)[0]
    common.align(fkHandCtrl, fkChain[2])
    cmds.parent(fkHandCtrl, fkLowArmCtrl)
    
    cmds.parentConstraint(fkUpArmCtrl, fkChain[0])
    cmds.parentConstraint(fkLowArmCtrl, fkChain[1])
    cmds.parentConstraint(fkHandCtrl, fkChain[2])
    
    # add extend attrs
    for ctrl in [fkLowArmCtrl, fkHandCtrl]:
        cmds.addAttr( ctrl, longName='extend', at='double', keyable=True )
        extend_pma = cmds.createNode('plusMinusAverage', name='%s_extend_pma' % ctrl)
        cmds.setAttr('%s.input1D[0]' % extend_pma, cmds.getAttr('%s.tx' % ctrl))
        if side == 'lf':
            cmds.setAttr('%s.operation' % extend_pma, 2)
        cmds.connectAttr('%s.extend' % ctrl, '%s.input1D[1]' % extend_pma)
        cmds.connectAttr('%s.output1D' % extend_pma, '%s.tx' % ctrl)
    
    ##################################################################################################################################### IK ctrls ####
    ikGrp = cmds.group(empty=1, name='%s_arm_ik_grp' % side)
    cmds.parent(ikGrp, root)
    cmds.connectAttr('%s.outputX' % stateRev, '%s.visibility' % ikGrp)
    
    # IK hand
    ikHandCtrl = controls.boxCtrl(name='%s_hand_ik_ctrl' % side, size=10)
    common.align(ikHandCtrl, resultChain[2], orient=0)
    cmds.parent(ikHandCtrl, ikGrp)
    common.insertGroup(ikHandCtrl)
    
    cmds.addAttr( ikHandCtrl, longName='stretch', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=True )
    cmds.addAttr( ikHandCtrl, longName='extend', at='double', keyable=True )
    cmds.addAttr( ikHandCtrl, longName='pin', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=True )
    
    # IK Elbow
    ikElbowCtrl = controls.crossCtrl(name='%s_elbow_ik_ctrl' % side, size=10)
    
    pvAxis = '-z'
    if side == 'rt':
        pvAxis='z'
    pv = common.placePoleVector(node1=resultChain[0], node2=resultChain[1], node3=resultChain[2], axis=pvAxis)
    cmds.setAttr('%s.t' % ikElbowCtrl, pv[0], pv[1], pv[2])
    cmds.parent(ikElbowCtrl, ikGrp)
    common.insertGroup(ikElbowCtrl)
    
    # IK Solvers
    ikHandle = cmds.ikHandle( solver='ikRPsolver', name='%s_arm_ikHandle' % side, startJoint=ikChain[ 0 ], endEffector=ikChain[ 2 ] )[ 0 ]
    common.align(ikHandle, resultChain[2])
    cmds.poleVectorConstraint(ikElbowCtrl, ikHandle)
    cmds.parent(ikHandle, ikHandCtrl)
    
    endIkHandle = cmds.ikHandle( solver='ikSCsolver', name='%s_arm_end_ikHandle' % side, startJoint=ikChain[ 2 ], endEffector=ikChain[ 3 ] )[ 0 ]
    common.align(endIkHandle, resultChain[3])
    cmds.parent(endIkHandle, ikHandCtrl)
    cmds.setAttr('%s.rotateX' % endIkHandle, 0)
    
    if side == 'lf':
        cmds.setAttr('%s.preferredAngleY' % ikChain[1], -90)
    
    # Set up ik / fk blending
    for i in range(4):
        common.blendAttrs(targ1=ikChain[i], targ2=fkChain[i], driven=resultChain[i], blendAttr='%s.state' % settingsCtrl)
    
    ############################################################################################################################## Stretchy IK
    # upArm to wrist measure
    armDist = measure.build(start=resultChain[0], end=resultChain[2], name='%s_armDist' % side)
    cmds.parent(armDist['start'], const)
    cmds.parent(armDist['xform'], const)
    cmds.parent(armDist['end'], ikHandCtrl)
    
    # upArm to elbow measure
    upArmDist = measure.build(start=resultChain[0], end=ikElbowCtrl, startLoc=armDist['start'], name='%s_upArmDist' % side)
    cmds.parent(upArmDist['xform'], const)
    cmds.parent(upArmDist['end'], ikElbowCtrl)
    
    # elbow to wrist measure
    lowArmDist = measure.build(start=ikElbowCtrl, end=ikHandCtrl, startLoc=upArmDist['end'], endLoc=armDist['end'], name='%s_lowArmDist' % side)
    cmds.parent(lowArmDist['xform'], const)
    
    # Utility node creation
    stretch_md = cmds.createNode('multiplyDivide', name='%s_arm_stretchFactor_md' % side)
    squash_md = cmds.createNode('multiplyDivide', name='%s_arm_squashFactor_md' % side)
    stretch_cond = cmds.createNode('condition', name='%s_arm_stretchFactor_cond' % side)
    extend_pma = cmds.createNode('plusMinusAverage', name='%s_arm_extend_pma' % side)
    
    upArmStretch_md = cmds.createNode('multiplyDivide', name='%s_upArm_stretch_md' % side)
    upArmStretchAmount_bc = cmds.createNode('blendColors', name='%s_upArm_stretchAmount_bc' % side)
    upArmPinAmount_bc = cmds.createNode('blendColors', name='%s_upArm_pinAmount_bc' % side)
    
    lowArmStretch_md = cmds.createNode('multiplyDivide', name='%s_lowArm_stretch_md' % side)
    lowArmStretchAmount_bc = cmds.createNode('blendColors', name='%s_lowArm_stretchAmount_bc' % side)
    lowArmPinAmount_bc = cmds.createNode('blendColors', name='%s_lowArm_pinAmount_bc' % side)
    
    extendGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_arm_extendGlobalScale_md' % side)
    armDistGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_armDist_globalScale_md' % side)
    upArmDistGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_upArmDistGlobalScale_md' % side)
    lowArmDistGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_lowArmDistGlobalScale_md' % side)
    
    # Connect up graph
    cmds.connectAttr('%s.extend' % ikHandCtrl, '%s.input1X' % extendGlobalScale_md)
    
    cmds.connectAttr('%s.distance' % armDist['shape'], '%s.input1X' % armDistGlobalScale_md)
    cmds.setAttr('%s.operation' % armDistGlobalScale_md, 2)
    
    cmds.connectAttr('%s.distance' % upArmDist['shape'], '%s.input1X' % upArmDistGlobalScale_md)
    cmds.setAttr('%s.operation' % upArmDistGlobalScale_md, 2)
    
    cmds.connectAttr('%s.distance' % lowArmDist['shape'], '%s.input1X' % lowArmDistGlobalScale_md)
    cmds.setAttr('%s.operation' % lowArmDistGlobalScale_md, 2)
    
    if globalScaleAttr:
        cmds.connectAttr(globalScaleAttr, '%s.input2X' % armDistGlobalScale_md )
        cmds.connectAttr(globalScaleAttr, '%s.input2X' % upArmDistGlobalScale_md )
        cmds.connectAttr(globalScaleAttr, '%s.input2X' % lowArmDistGlobalScale_md )
    else:
        cmds.setAttr('%s.input2X' % armDistGlobalScale_md, 1)
        cmds.setAttr('%s.input2X' % upArmDistGlobalScale_md, 1)
        cmds.setAttr('%s.input2X' % lowArmDistGlobalScale_md, 1)
        
    upArmLength = math.fabs(cmds.getAttr('%s.tx' % resultChain[1]))
    lowArmLength = math.fabs(cmds.getAttr('%s.tx' % resultChain[2]))
    
    cmds.connectAttr('%s.outputX' % extendGlobalScale_md, '%s.input1D[0]' % extend_pma)
    cmds.setAttr('%s.input1D[1]' % extend_pma, upArmLength + lowArmLength)
    
    cmds.connectAttr('%s.output1D' % extend_pma, '%s.input1X' % squash_md)
    cmds.setAttr('%s.input2X' % squash_md, upArmLength + lowArmLength)
    cmds.setAttr('%s.operation' % squash_md, 2)
    
    cmds.connectAttr('%s.outputX' % armDistGlobalScale_md, '%s.input1X' % stretch_md)
    cmds.setAttr('%s.input2X' % stretch_md, upArmLength + lowArmLength)
    cmds.setAttr('%s.operation' % stretch_md, 2)
    
    cmds.connectAttr('%s.outputX' % armDistGlobalScale_md, '%s.firstTerm' % stretch_cond)
    cmds.connectAttr('%s.output1D' % extend_pma, '%s.secondTerm' % stretch_cond)
    cmds.connectAttr('%s.outputX' % stretch_md, '%s.colorIfTrueR' % stretch_cond)
    cmds.connectAttr('%s.outputX' % squash_md, '%s.colorIfFalseR' % stretch_cond)
    cmds.setAttr('%s.operation' % stretch_cond, 2)
    
    cmds.connectAttr('%s.outColorR' % stretch_cond, '%s.input1X' % upArmStretch_md)
    cmds.setAttr('%s.input2X' % upArmStretch_md, upArmLength)
    
    cmds.connectAttr('%s.outColorR' % stretch_cond, '%s.input1X' % lowArmStretch_md)
    cmds.setAttr('%s.input2X' % lowArmStretch_md, lowArmLength)
    
    cmds.connectAttr('%s.stretch' % ikHandCtrl, '%s.blender' % upArmStretchAmount_bc)
    cmds.connectAttr('%s.outputX' % upArmStretch_md, '%s.color1R' % upArmStretchAmount_bc)
    cmds.setAttr('%s.color2R' % upArmStretchAmount_bc, upArmLength)
    
    cmds.connectAttr('%s.stretch' % ikHandCtrl, '%s.blender' % lowArmStretchAmount_bc)
    cmds.connectAttr('%s.outputX' % lowArmStretch_md, '%s.color1R' % lowArmStretchAmount_bc)
    cmds.setAttr('%s.color2R' % lowArmStretchAmount_bc, lowArmLength)
    
    cmds.connectAttr('%s.pin' % ikHandCtrl, '%s.blender' % upArmPinAmount_bc)
    cmds.connectAttr('%s.outputX' % upArmDistGlobalScale_md, '%s.color1R' % upArmPinAmount_bc)
    cmds.connectAttr('%s.outputR' % upArmStretchAmount_bc, '%s.color2R' % upArmPinAmount_bc)
    
    cmds.connectAttr('%s.pin' % ikHandCtrl, '%s.blender' % lowArmPinAmount_bc)
    cmds.connectAttr('%s.outputX' % lowArmDistGlobalScale_md, '%s.color1R' % lowArmPinAmount_bc)
    cmds.connectAttr('%s.outputR' % lowArmStretchAmount_bc, '%s.color2R' % lowArmPinAmount_bc)
    
    if side == 'lf':
        upArmPinAmount_uc = cmds.createNode('unitConversion', name='%s_upArmPinAmount_uc')
        cmds.setAttr('%s.conversionFactor' % upArmPinAmount_uc, -1)
        cmds.connectAttr('%s.outputR' % upArmPinAmount_bc, '%s.input' % upArmPinAmount_uc)
        cmds.connectAttr('%s.output' % upArmPinAmount_uc, '%s.tx' % ikChain[1])
        
        lowArmPinAmount_uc = cmds.createNode('unitConversion', name='%s_lowArmPinAmount_uc')
        cmds.setAttr('%s.conversionFactor' % lowArmPinAmount_uc, -1)
        cmds.connectAttr('%s.outputR' % lowArmPinAmount_bc, '%s.input' % lowArmPinAmount_uc)
        cmds.connectAttr('%s.output' % lowArmPinAmount_uc, '%s.tx' % ikChain[2])
    else:  
        cmds.connectAttr('%s.outputR' % upArmPinAmount_bc, '%s.tx' % ikChain[1])
        cmds.connectAttr('%s.outputR' % lowArmPinAmount_bc, '%s.tx' % ikChain[2])
    
    
    ############################################################################################################################# Twist extration
    upArmNonRoll = nonRoll.build(joint=resultChain[0], name='%s_upArm' % side)
    cmds.parent(upArmNonRoll['main_grp'], const)
    
    lowArmNonRoll = nonRoll.build(joint=resultChain[1], name='%s_lowArm' % side)
    cmds.parent(lowArmNonRoll['main_grp'], upArmNonRoll['nonRoll'])
    
    wristNonRoll = nonRoll.build(joint=resultChain[2], name='%s_wrist' % side)
    cmds.parent(wristNonRoll['main_grp'], resultChain[1])
    
    
    ############################################################################################################################# Bendy arm
    bendGrp = cmds.group(empty=1, name='%s_arm_bend_grp' % side)
    cmds.parent(bendGrp, root)
    cmds.connectAttr('%s.bendy_ctrls' % settingsCtrl, '%s.visibility' % bendGrp)
    
    # Elbow ctrl
    bendyElbowCtrl = controls.squareCtrl(name='%s_elbow_bend_ctrl' % side, axis='x', size=10)
    cmds.parent(bendyElbowCtrl, bendGrp)
    bendyElbowGrp = common.insertGroup(bendyElbowCtrl)
    bendyElbowGrp = cmds.rename(bendyElbowGrp, '%s_elbow_bend_grp' % side)
    orientConstraint = cmds.orientConstraint(resultChain[0], resultChain[1], bendyElbowGrp)[0]
    cmds.setAttr('%s.interpType' % orientConstraint, 2)
    cmds.pointConstraint(resultChain[1], bendyElbowGrp)
    cmds.addAttr(settingsCtrl, longName='auto_bend', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=1)
    
    # Auto / Manual elbow bend
    # In
    bendyElbowInConstGrp = cmds.group(empty=1, name='%s_elbow_bend_in_const_grp' % side)
    common.align(bendyElbowInConstGrp, resultChain[0])
    upArmPoints = common.pointsAlongVector(resultChain[0], resultChain[1], divisions=3)
    cmds.setAttr('%s.t' % bendyElbowInConstGrp, upArmPoints[2][0], upArmPoints[2][1], upArmPoints[2][2])
    cmds.parent(bendyElbowInConstGrp, bendGrp)
    
    bendyElbowInCtrl = controls.squareCtrl(name='%s_elbow_bend_in_ctrl' % side, axis='x', size=7.5)
    common.align(bendyElbowInCtrl, bendyElbowInConstGrp)
    cmds.parent(bendyElbowInCtrl, bendyElbowInConstGrp)
    
    bendyElbowInManual = cmds.group(empty=1, name='%s_elbow_bend_in_manual_targ' % side)
    common.align(bendyElbowInManual, bendyElbowInConstGrp)
    cmds.parent(bendyElbowInManual, resultChain[0])
    cmds.pointConstraint(bendyElbowCtrl, resultChain[0], bendyElbowInManual)
    cmds.pointConstraint(bendyElbowCtrl, bendyElbowInManual, e=1, w=2.0)
    
    bendyElbowInAuto = cmds.group(empty=1, name='%s_elbow_bend_in_auto_targ' % side)
    common.align(bendyElbowInAuto, bendyElbowInConstGrp)
    cmds.parent(bendyElbowInAuto, bendyElbowCtrl)
    
    parentConstraint = cmds.parentConstraint(bendyElbowInManual, bendyElbowInAuto, bendyElbowInConstGrp)[0]
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.%sW1' % (parentConstraint, bendyElbowInAuto))
    rev = cmds.createNode('reverse', name='%s_elbow_bend_auto_rev')
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.inputX' % rev)
    cmds.connectAttr('%s.outputX' % rev, '%s.%sW0' % (parentConstraint, bendyElbowInManual))
    
    # out
    bendyElbowOutConstGrp = cmds.group(empty=1, name='%s_elbow_bend_out_const_grp' % side)
    common.align(bendyElbowOutConstGrp, resultChain[1])
    lowArmPoints = common.pointsAlongVector(resultChain[1], resultChain[2], divisions=3)
    cmds.setAttr('%s.t' % bendyElbowOutConstGrp, lowArmPoints[1][0], lowArmPoints[1][1], lowArmPoints[1][2])
    cmds.parent(bendyElbowOutConstGrp, bendGrp)
    
    bendyElbowOutCtrl = controls.squareCtrl(name='%s_elbow_bend_out_ctrl' % side, axis='x', size=7.5)
    common.align(bendyElbowOutCtrl, bendyElbowOutConstGrp)
    cmds.parent(bendyElbowOutCtrl, bendyElbowOutConstGrp)
    
    bendyElbowOutManual = cmds.group(empty=1, name='%s_elbow_bend_out_manual_targ' % side)
    common.align(bendyElbowOutManual, bendyElbowOutConstGrp)
    cmds.parent(bendyElbowOutManual, resultChain[1])
    cmds.pointConstraint(bendyElbowCtrl, resultChain[2], bendyElbowOutManual)
    cmds.pointConstraint(bendyElbowCtrl, bendyElbowOutManual, e=1, w=2.0)
    
    bendyElbowOutAuto = cmds.group(empty=1, name='%s_elbow_bend_out_auto_targ' % side)
    common.align(bendyElbowOutAuto, bendyElbowOutConstGrp)
    cmds.parent(bendyElbowOutAuto, bendyElbowCtrl)
    
    parentConstraint = cmds.parentConstraint(bendyElbowOutManual, bendyElbowOutAuto, bendyElbowOutConstGrp)[0]
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.%sW1' % (parentConstraint, bendyElbowOutAuto))
    rev = cmds.createNode('reverse', name='%s_elbow_bend_auto_rev')
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.inputX' % rev)
    cmds.connectAttr('%s.outputX' % rev, '%s.%sW0' % (parentConstraint, bendyElbowOutManual))
    
    # Shldr out
    bendyShldrConstGrp = cmds.group(empty=1, name='%s_shldr_bend_const_grp' % side)
    common.align(bendyShldrConstGrp, resultChain[0])
    cmds.parent(bendyShldrConstGrp, bendGrp)
    
    bendyShldrCtrl = controls.squareCtrl(name='%s_shldr_bend_ctrl' % side, axis='x', size=7.5)
    common.align(bendyShldrCtrl, bendyShldrConstGrp)
    cmds.parent(bendyShldrCtrl, bendyShldrConstGrp)
    cmds.pointConstraint(bendyElbowCtrl, resultChain[0], bendyShldrConstGrp)
    cmds.pointConstraint(bendyElbowCtrl, bendyShldrConstGrp, e=1, w=0.5)
    cmds.orientConstraint(resultChain[0], bendyShldrConstGrp)
    
    # Wrist in
    bendyWristConstGrp = cmds.group(empty=1, name='%s_wrist_bend_const_grp' % side)
    common.align(bendyWristConstGrp, resultChain[1])
    cmds.parent(bendyWristConstGrp, bendGrp)
    
    bendyWristCtrl = controls.squareCtrl(name='%s_wrist_bend_ctrl' % side, axis='x', size=7.5)
    common.align(bendyWristCtrl, bendyWristConstGrp)
    cmds.parent(bendyWristCtrl, bendyWristConstGrp)
    cmds.pointConstraint(bendyElbowCtrl, resultChain[2], bendyWristConstGrp)
    cmds.pointConstraint(bendyElbowCtrl, bendyWristConstGrp, e=1, w=0.5)
    cmds.orientConstraint(resultChain[1], bendyWristConstGrp)
    
        
    ############################################################################################################################# Curve segments
    defJnts_grp = cmds.group(empty=1, name='%s_arm_defJnts_grp' % side)
    cmds.parent(defJnts_grp, root)
    
    # up arm
    upArmSeg = cmds.group(empty=1, name='%s_upArm_segment_grp' % side)
    cmds.parent(upArmSeg, defJnts_grp)
    cmds.setAttr('%s.inheritsTransform' % upArmSeg, 0)
    
    crv = curve.curveBetweenNodes(start=upArm, end=lowArm, name='%s_upArm' % side)
    cmds.parent(crv, const)
    
    mpNodes = curve.nodesAlongCurve(crv=crv, numNodes=twistJoints, name='%s_upArm' % side, upNode=upArmNonRoll['nonRoll'])
    cmds.parent(mpNodes['grps'], upArmSeg)
    
    roll_uc = cmds.createNode('unitConversion', name='%s_upArm_roll_uc' % side)
    cmds.setAttr('%s.conversionFactor' % roll_uc, 1.0)
    cmds.connectAttr('%s.rotateX' % lowArmNonRoll['info'], '%s.input' % roll_uc)
    
    elbowRoll_uc = cmds.createNode('unitConversion', name='%s_upArm_elbowRoll_uc' % side)
    cmds.setAttr('%s.conversionFactor' % elbowRoll_uc, 1.0)
    cmds.connectAttr('%s.rotateX' % bendyElbowCtrl, '%s.input' % elbowRoll_uc)
    
    roll_pma = cmds.createNode('plusMinusAverage', name='%s_upArm_roll_pma' % side)
    cmds.connectAttr('%s.output' % roll_uc, '%s.input1D[0]' % roll_pma)
    cmds.connectAttr('%s.output' % elbowRoll_uc, '%s.input1D[1]' % roll_pma)
    
    for i in range(len(mpNodes['mpNodes'])):
        # Create child Joint
        cmds.select(clear=1)
        j = cmds.joint(name='%s_upArm_%s_defJnt' % (side, i))
        common.align(j, mpNodes['grps'][i])
        cmds.parent(j, mpNodes['grps'][i])
        
        totalRoll_uc = cmds.createNode('unitConversion', name='%s_upArm_totalRoll_%s_uc' % (side, i+1))
        if side == 'lf':
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc,  (1.0 / (twistJoints-1) * i)*-1)
        else:
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc,  1.0 / (twistJoints-1) * i)
        cmds.connectAttr('%s.output1D' % roll_pma, '%s.input' % totalRoll_uc)
        cmds.connectAttr('%s.output' % totalRoll_uc, '%s.frontTwist' % mpNodes['mpNodes'][i])
    
    upArmCrvJnts = curve.bindCurve(crv=crv)
    cmds.parent(upArmCrvJnts[0], resultChain[0])
    cmds.parent(upArmCrvJnts[1], bendyShldrCtrl)
    cmds.parent(upArmCrvJnts[2], bendyElbowInCtrl)
    cmds.parent(upArmCrvJnts[3], bendyElbowCtrl)
    
    # low arm
    lowArmSeg = cmds.group(empty=1, name='%s_lowArm_segment_grp' % side)
    cmds.parent(lowArmSeg, defJnts_grp)
    cmds.setAttr('%s.inheritsTransform' % lowArmSeg, 0)
    
    crv = curve.curveBetweenNodes(start=lowArm, end=wrist, name='%s_lowArm' % side)
    cmds.parent(crv, const)
    
    mpNodes = curve.nodesAlongCurve(crv=crv, numNodes=twistJoints, name='%s_lowArm' % side, upNode=resultChain[1])
    cmds.parent(mpNodes['grps'], lowArmSeg)
    
    for i in range(len(mpNodes['mpNodes'])):
        # Create child Joint
        cmds.select(clear=1)
        j = cmds.joint(name='%s_lowArm_%s_defJnt' % (side, i))
        common.align(j, mpNodes['grps'][i])
        cmds.parent(j, mpNodes['grps'][i])
        
        roll_uc = cmds.createNode('unitConversion', name='%s_lowArm_roll_%s_uc' % (side, i+1))
        cmds.setAttr('%s.conversionFactor' % roll_uc, 1.0 / (twistJoints-1) * i)
        cmds.connectAttr('%s.rotateX' % wristNonRoll['info'], '%s.input' % roll_uc)
        
        elbowRoll_uc = cmds.createNode('unitConversion', name='%s_lowArm_elbowRoll_%s_uc' % (side, i+1))
        cmds.setAttr('%s.conversionFactor' % elbowRoll_uc, 1.0 - (1.0 / (twistJoints-1) * i))
        cmds.connectAttr('%s.rotateX' % bendyElbowCtrl, '%s.input' % elbowRoll_uc)
        
        roll_pma = cmds.createNode('plusMinusAverage', name='%s_lowArm_roll_%s_pma' % (side, i+1))
        cmds.connectAttr('%s.output' % roll_uc, '%s.input1D[0]' % roll_pma)
        cmds.connectAttr('%s.output' % elbowRoll_uc, '%s.input1D[1]' % roll_pma)
        
        totalRoll_uc = cmds.createNode('unitConversion', name='%s_lowArm_totalRoll_%s_uc' % (side, i+1))
        if side == 'lf':
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc, -1.0)
        else:
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc, 1.0)
        cmds.connectAttr('%s.output1D' % roll_pma, '%s.input' % totalRoll_uc)
        cmds.connectAttr('%s.output' % totalRoll_uc, '%s.frontTwist' % mpNodes['mpNodes'][i])
    
    lowArmCrvJnts = curve.bindCurve(crv=crv)
    cmds.parent(lowArmCrvJnts[0], bendyElbowCtrl)
    cmds.parent(lowArmCrvJnts[1], bendyElbowOutCtrl)
    cmds.parent(lowArmCrvJnts[2], bendyWristCtrl)
    cmds.parent(lowArmCrvJnts[3], resultChain[2])
    
    ############################################################################################################################################## CLEANUP
    if cleanup:
        cmds.setAttr('%s.visibility' % const, 0)
        common.attrCtrl(lock=True, keyable=False, channelBox=False, nodeList=[const, bendyElbowCtrl], attrList=['visibility'])
        
        common.attrCtrl(lock=True, keyable=False, channelBox=False,
                        nodeList=[fkUpArmCtrl, fkLowArmCtrl, fkHandCtrl],
                        attrList=['visibility', 'tx', 'ty', 'tz', 'sx', 'sy', 'sz'])
        
        common.attrCtrl(lock=True, keyable=False, channelBox=False,
                        nodeList=[ikHandCtrl,],
                        attrList=['visibility', 'sx', 'sy', 'sz'])
        
        common.attrCtrl(lock=True, keyable=False, channelBox=False,
                        nodeList=[ikElbowCtrl, bendyShldrCtrl, bendyElbowInCtrl, bendyElbowOutCtrl, bendyWristCtrl],
                        attrList=['visibility', 'sx', 'sy', 'sz'])
        
    ############################################################################################################################################## RETURN
    returnDict={
                'upArm_fk_ctrl':fkUpArmCtrl,
                'lowArm_fk_ctrl':fkLowArmCtrl,
                'hand_fk_ctrl':fkHandCtrl,
                'hand_ik_ctrl':ikHandCtrl,
                'elbow_ik_ctrl': ikElbowCtrl,
                'settings':settingsCtrl,
                'elbow_bend_ctrl':bendyElbowCtrl,
                'shldr_bend_ctrl':bendyShldrCtrl,
                'elbow_in_bend_ctrl':bendyElbowInCtrl,
                'elbow_out_bend_ctrl':bendyElbowInCtrl,
                'root':root,
                'const':const
                }
    
    return returnDict
        
        
        
        
        
        
        
        
        
        