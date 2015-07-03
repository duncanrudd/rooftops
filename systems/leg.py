import maya.cmds as cmds
import math
from ROOFTOPS.core import common
from ROOFTOPS.systems import curve, controls, measure, nonRoll

def build(upLeg=None, lowLeg=None, ankle=None, end=None, side='lf', twistJoints=5, globalScaleAttr=None, cleanup=0):
    '''
    makes a triple chain leg using a set of 4 existing hierarchical joints
    
    '''
    #Validation
    if not upLeg or not lowLeg or not ankle or not end:
        if len(cmds.ls(sl=1)) == 4:
            upLeg = cmds.ls(sl=1)[0]
            lowLeg = cmds.ls(sl=1)[1]
            ankle = cmds.ls(sl=1)[2]
            end = cmds.ls(sl=1)[3]
        else:
            return common.showDialog( 'Argument Error', 'Please supply 4 hierarchical joints' )
    
    # Root group
    root = cmds.group(empty=1, name='%s_leg_grp' % side)
    
    #Constrain group which is aligned to the first joint and can be used to attach the leg to a shoulder
    const = cmds.group(empty=1, name='%s_leg_const_grp' % side)
    common.align(const, upLeg)
    cmds.parent(const, root)
    
    # result chainw
    dupes = cmds.duplicate(upLeg, rc=1)
    resultChain = []
    for i in range(4):
        jnt = cmds.rename(dupes[i], '%s_%s_result_jnt' %(side, ['upLeg', 'lowLeg', 'ankle', 'end'][i]) )
        resultChain.append(jnt)
        
    cmds.parent(resultChain[0], const)
    
    # fk chain
    dupes = cmds.duplicate(resultChain[0], rc=1)
    fkChain = []
    for i in range(4):
        jnt = cmds.rename(dupes[i], '%s_%s_fk_jnt' %(side, ['upLeg', 'lowLeg', 'ankle', 'end'][i]) )
        fkChain.append(jnt)
        
    
    # ik chain
    dupes = cmds.duplicate(resultChain[0], rc=1)
    ikChain = []
    for i in range(4):
        jnt = cmds.rename(dupes[i], '%s_%s_ik_jnt' %(side, ['upLeg', 'lowLeg', 'ankle', 'end'][i]) )
        ikChain.append(jnt)
        
    # Settings ctrl
    settingsCtrl = controls.crossCtrl(name='%s_leg_settings_ctrl' % side)
    settingsShape = common.getShape(settingsCtrl)
    common.align(settingsCtrl, const)
    cmds.parent(settingsCtrl, root)
    # ik / fk attr
    cmds.addAttr( settingsCtrl, longName='state', at='enum', enumName='ik:fk', keyable=True )
    stateRev = cmds.createNode('reverse', name='%s_leg_state_rev' % side)
    cmds.connectAttr('%s.state' % settingsCtrl, '%s.inputX' % stateRev)
    # bendy ctrls switch
    cmds.addAttr( settingsCtrl, longName='bendy_ctrls', at='enum', enumName='hide:show', keyable=True )
    
    ##################################################################################################################################### FK Ctrls
    fkGrp = cmds.group(empty=1, name='%s_leg_fk_grp' % side)
    cmds.parent(fkGrp, root)
    cmds.connectAttr('%s.state' % settingsCtrl, '%s.visibility' % fkGrp)
    
    # fk up leg
    fkUpLegCtrl = controls.circleBumpCtrl(name='%s_upLeg_fk_ctrl' % side, axis='x', radius=10)[0]
    common.align(fkUpLegCtrl, fkChain[0])
    cmds.parent(fkUpLegCtrl, fkGrp)
    common.insertGroup(fkUpLegCtrl)
    
    # fk low leg
    fkLowLegCtrl = controls.circleBumpCtrl(name='%s_lowLeg_fk_ctrl' % side, axis='x', radius=10)[0]
    common.align(fkLowLegCtrl, fkChain[1])
    cmds.parent(fkLowLegCtrl, fkUpLegCtrl)
    
    # fk foot
    fkFootCtrl = controls.circleBumpCtrl(name='%s_foot_fk_ctrl' % side, axis='x', radius=10)[0]
    common.align(fkFootCtrl, fkChain[2])
    cmds.parent(fkFootCtrl, fkLowLegCtrl)
    
    cmds.parentConstraint(fkUpLegCtrl, fkChain[0])
    cmds.parentConstraint(fkLowLegCtrl, fkChain[1])
    cmds.parentConstraint(fkFootCtrl, fkChain[2])
    
    # add extend attrs
    for ctrl in [fkLowLegCtrl, fkFootCtrl]:
        cmds.addAttr( ctrl, longName='extend', at='double', keyable=True )
        extend_pma = cmds.createNode('plusMinusAverage', name='%s_extend_pma' % ctrl)
        cmds.setAttr('%s.input1D[0]' % extend_pma, cmds.getAttr('%s.tx' % ctrl))
        if side == 'lf':
            cmds.setAttr('%s.operation' % extend_pma, 2)
        cmds.connectAttr('%s.extend' % ctrl, '%s.input1D[1]' % extend_pma)
        cmds.connectAttr('%s.output1D' % extend_pma, '%s.tx' % ctrl)
    
    ##################################################################################################################################### IK ctrls ####
    ikGrp = cmds.group(empty=1, name='%s_leg_ik_grp' % side)
    cmds.parent(ikGrp, root)
    cmds.connectAttr('%s.outputX' % stateRev, '%s.visibility' % ikGrp)
    
    # IK foot
    ikFootCtrl = controls.boxCtrl(name='%s_foot_ik_ctrl' % side, size=10)
    common.align(ikFootCtrl, resultChain[2], orient=0)
    cmds.parent(ikFootCtrl, ikGrp)
    common.insertGroup(ikFootCtrl)
    
    cmds.addAttr( ikFootCtrl, longName='stretch', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=True )
    cmds.addAttr( ikFootCtrl, longName='extend', at='double', keyable=True )
    cmds.addAttr( ikFootCtrl, longName='pin', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=True )
    
    # IK Knee
    ikKneeCtrl = controls.crossCtrl(name='%s_knee_ik_ctrl' % side, size=10)
    
    pvAxis = '-z'
    if side == 'rt':
        pvAxis='z'
    pv = common.placePoleVector(node1=resultChain[0], node2=resultChain[1], node3=resultChain[2], axis=pvAxis)
    cmds.setAttr('%s.t' % ikKneeCtrl, pv[0], pv[1], pv[2])
    cmds.parent(ikKneeCtrl, ikGrp)
    common.insertGroup(ikKneeCtrl)
    
    # IK Solvers
    ikHandle = cmds.ikHandle( solver='ikRPsolver', name='%s_leg_ikHandle' % side, startJoint=ikChain[ 0 ], endEffector=ikChain[ 2 ] )[ 0 ]
    common.align(ikHandle, resultChain[2])
    cmds.poleVectorConstraint(ikKneeCtrl, ikHandle)
    cmds.parent(ikHandle, ikFootCtrl)
    
    endIkFootle = cmds.ikHandle( solver='ikSCsolver', name='%s_leg_end_ikHandle' % side, startJoint=ikChain[ 2 ], endEffector=ikChain[ 3 ] )[ 0 ]
    common.align(endIkFootle, resultChain[3])
    cmds.parent(endIkFootle, ikFootCtrl)
    cmds.setAttr('%s.rotateX' % endIkFootle, 0)
    
    if side == 'lf':
        cmds.setAttr('%s.preferredAngleY' % ikChain[1], -90)
    
    # Set up ik / fk blending
    for i in range(4):
        common.blendAttrs(targ1=ikChain[i], targ2=fkChain[i], driven=resultChain[i], blendAttr='%s.state' % settingsCtrl)
    
    ############################################################################################################################## Stretchy IK
    # upLeg to ankle measure
    legDist = measure.build(start=resultChain[0], end=resultChain[2], name='%s_legDist' % side)
    cmds.parent(legDist['start'], const)
    cmds.parent(legDist['xform'], const)
    cmds.parent(legDist['end'], ikFootCtrl)
    
    # upLeg to knee measure
    upLegDist = measure.build(start=resultChain[0], end=ikKneeCtrl, startLoc=legDist['start'], name='%s_upLegDist' % side)
    cmds.parent(upLegDist['xform'], const)
    cmds.parent(upLegDist['end'], ikKneeCtrl)
    
    # knee to ankle measure
    lowLegDist = measure.build(start=ikKneeCtrl, end=ikFootCtrl, startLoc=upLegDist['end'], endLoc=legDist['end'], name='%s_lowLegDist' % side)
    cmds.parent(lowLegDist['xform'], const)
    
    # Utility node creation
    stretch_md = cmds.createNode('multiplyDivide', name='%s_leg_stretchFactor_md' % side)
    squash_md = cmds.createNode('multiplyDivide', name='%s_leg_squashFactor_md' % side)
    stretch_cond = cmds.createNode('condition', name='%s_leg_stretchFactor_cond' % side)
    extend_pma = cmds.createNode('plusMinusAverage', name='%s_leg_extend_pma' % side)
    
    upLegStretch_md = cmds.createNode('multiplyDivide', name='%s_upLeg_stretch_md' % side)
    upLegStretchAmount_bc = cmds.createNode('blendColors', name='%s_upLeg_stretchAmount_bc' % side)
    upLegPinAmount_bc = cmds.createNode('blendColors', name='%s_upLeg_pinAmount_bc' % side)
    
    lowLegStretch_md = cmds.createNode('multiplyDivide', name='%s_lowLeg_stretch_md' % side)
    lowLegStretchAmount_bc = cmds.createNode('blendColors', name='%s_lowLeg_stretchAmount_bc' % side)
    lowLegPinAmount_bc = cmds.createNode('blendColors', name='%s_lowLeg_pinAmount_bc' % side)
    
    extendGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_leg_extendGlobalScale_md' % side)
    legDistGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_legDist_globalScale_md' % side)
    upLegDistGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_upLegDistGlobalScale_md' % side)
    lowLegDistGlobalScale_md = cmds.createNode('multiplyDivide', name='%s_lowLegDistGlobalScale_md' % side)
    
    # Connect up graph
    cmds.connectAttr('%s.extend' % ikFootCtrl, '%s.input1X' % extendGlobalScale_md)
    
    cmds.connectAttr('%s.distance' % legDist['shape'], '%s.input1X' % legDistGlobalScale_md)
    cmds.setAttr('%s.operation' % legDistGlobalScale_md, 2)
    
    cmds.connectAttr('%s.distance' % upLegDist['shape'], '%s.input1X' % upLegDistGlobalScale_md)
    cmds.setAttr('%s.operation' % upLegDistGlobalScale_md, 2)
    
    cmds.connectAttr('%s.distance' % lowLegDist['shape'], '%s.input1X' % lowLegDistGlobalScale_md)
    cmds.setAttr('%s.operation' % lowLegDistGlobalScale_md, 2)
    
    if globalScaleAttr:
        cmds.connectAttr(globalScaleAttr, '%s.input2X' % legDistGlobalScale_md )
        cmds.connectAttr(globalScaleAttr, '%s.input2X' % upLegDistGlobalScale_md )
        cmds.connectAttr(globalScaleAttr, '%s.input2X' % lowLegDistGlobalScale_md )
    else:
        cmds.setAttr('%s.input2X' % legDistGlobalScale_md, 1)
        cmds.setAttr('%s.input2X' % upLegDistGlobalScale_md, 1)
        cmds.setAttr('%s.input2X' % lowLegDistGlobalScale_md, 1)
        
    upLegLength = math.fabs(cmds.getAttr('%s.tx' % resultChain[1]))
    lowLegLength = math.fabs(cmds.getAttr('%s.tx' % resultChain[2]))
    
    cmds.connectAttr('%s.outputX' % extendGlobalScale_md, '%s.input1D[0]' % extend_pma)
    cmds.setAttr('%s.input1D[1]' % extend_pma, upLegLength + lowLegLength)
    
    cmds.connectAttr('%s.output1D' % extend_pma, '%s.input1X' % squash_md)
    cmds.setAttr('%s.input2X' % squash_md, upLegLength + lowLegLength)
    cmds.setAttr('%s.operation' % squash_md, 2)
    
    cmds.connectAttr('%s.outputX' % legDistGlobalScale_md, '%s.input1X' % stretch_md)
    cmds.setAttr('%s.input2X' % stretch_md, upLegLength + lowLegLength)
    cmds.setAttr('%s.operation' % stretch_md, 2)
    
    cmds.connectAttr('%s.outputX' % legDistGlobalScale_md, '%s.firstTerm' % stretch_cond)
    cmds.connectAttr('%s.output1D' % extend_pma, '%s.secondTerm' % stretch_cond)
    cmds.connectAttr('%s.outputX' % stretch_md, '%s.colorIfTrueR' % stretch_cond)
    cmds.connectAttr('%s.outputX' % squash_md, '%s.colorIfFalseR' % stretch_cond)
    cmds.setAttr('%s.operation' % stretch_cond, 2)
    
    cmds.connectAttr('%s.outColorR' % stretch_cond, '%s.input1X' % upLegStretch_md)
    cmds.setAttr('%s.input2X' % upLegStretch_md, upLegLength)
    
    cmds.connectAttr('%s.outColorR' % stretch_cond, '%s.input1X' % lowLegStretch_md)
    cmds.setAttr('%s.input2X' % lowLegStretch_md, lowLegLength)
    
    cmds.connectAttr('%s.stretch' % ikFootCtrl, '%s.blender' % upLegStretchAmount_bc)
    cmds.connectAttr('%s.outputX' % upLegStretch_md, '%s.color1R' % upLegStretchAmount_bc)
    cmds.setAttr('%s.color2R' % upLegStretchAmount_bc, upLegLength)
    
    cmds.connectAttr('%s.stretch' % ikFootCtrl, '%s.blender' % lowLegStretchAmount_bc)
    cmds.connectAttr('%s.outputX' % lowLegStretch_md, '%s.color1R' % lowLegStretchAmount_bc)
    cmds.setAttr('%s.color2R' % lowLegStretchAmount_bc, lowLegLength)
    
    cmds.connectAttr('%s.pin' % ikFootCtrl, '%s.blender' % upLegPinAmount_bc)
    cmds.connectAttr('%s.outputX' % upLegDistGlobalScale_md, '%s.color1R' % upLegPinAmount_bc)
    cmds.connectAttr('%s.outputR' % upLegStretchAmount_bc, '%s.color2R' % upLegPinAmount_bc)
    
    cmds.connectAttr('%s.pin' % ikFootCtrl, '%s.blender' % lowLegPinAmount_bc)
    cmds.connectAttr('%s.outputX' % lowLegDistGlobalScale_md, '%s.color1R' % lowLegPinAmount_bc)
    cmds.connectAttr('%s.outputR' % lowLegStretchAmount_bc, '%s.color2R' % lowLegPinAmount_bc)
    
    if side == 'lf':
        upLegPinAmount_uc = cmds.createNode('unitConversion', name='%s_upLegPinAmount_uc')
        cmds.setAttr('%s.conversionFactor' % upLegPinAmount_uc, -1)
        cmds.connectAttr('%s.outputR' % upLegPinAmount_bc, '%s.input' % upLegPinAmount_uc)
        cmds.connectAttr('%s.output' % upLegPinAmount_uc, '%s.tx' % ikChain[1])
        
        lowLegPinAmount_uc = cmds.createNode('unitConversion', name='%s_lowLegPinAmount_uc')
        cmds.setAttr('%s.conversionFactor' % lowLegPinAmount_uc, -1)
        cmds.connectAttr('%s.outputR' % lowLegPinAmount_bc, '%s.input' % lowLegPinAmount_uc)
        cmds.connectAttr('%s.output' % lowLegPinAmount_uc, '%s.tx' % ikChain[2])
    else:  
        cmds.connectAttr('%s.outputR' % upLegPinAmount_bc, '%s.tx' % ikChain[1])
        cmds.connectAttr('%s.outputR' % lowLegPinAmount_bc, '%s.tx' % ikChain[2])
    
    
    ############################################################################################################################# Twist extration
    upLegNonRoll = nonRoll.build(joint=resultChain[0], name='%s_upLeg' % side)
    cmds.parent(upLegNonRoll['main_grp'], const)
    
    lowLegNonRoll = nonRoll.build(joint=resultChain[1], name='%s_lowLeg' % side)
    cmds.parent(lowLegNonRoll['main_grp'], upLegNonRoll['nonRoll'])
    
    ankleNonRoll = nonRoll.build(joint=resultChain[2], name='%s_ankle' % side)
    cmds.parent(ankleNonRoll['main_grp'], resultChain[1])
    
    
    ############################################################################################################################# Bendy leg
    bendGrp = cmds.group(empty=1, name='%s_leg_bend_grp' % side)
    cmds.parent(bendGrp, root)
    cmds.connectAttr('%s.bendy_ctrls' % settingsCtrl, '%s.visibility' % bendGrp)
    
    # Knee ctrl
    bendyKneeCtrl = controls.squareCtrl(name='%s_knee_bend_ctrl' % side, axis='x', size=10)
    cmds.parent(bendyKneeCtrl, bendGrp)
    bendyKneeGrp = common.insertGroup(bendyKneeCtrl)
    bendyKneeGrp = cmds.rename(bendyKneeGrp, '%s_knee_bend_grp' % side)
    orientConstraint = cmds.orientConstraint(resultChain[0], resultChain[1], bendyKneeGrp)[0]
    cmds.setAttr('%s.interpType' % orientConstraint, 2)
    cmds.pointConstraint(resultChain[1], bendyKneeGrp)
    cmds.addAttr(settingsCtrl, longName='auto_bend', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=1)
    
    # Auto / Manual knee bend
    # In
    bendyKneeInConstGrp = cmds.group(empty=1, name='%s_knee_bend_in_const_grp' % side)
    common.align(bendyKneeInConstGrp, resultChain[0])
    upLegPoints = common.pointsAlongVector(resultChain[0], resultChain[1], divisions=3)
    cmds.setAttr('%s.t' % bendyKneeInConstGrp, upLegPoints[2][0], upLegPoints[2][1], upLegPoints[2][2])
    cmds.parent(bendyKneeInConstGrp, bendGrp)
    
    bendyKneeInCtrl = controls.squareCtrl(name='%s_knee_bend_in_ctrl' % side, axis='x', size=7.5)
    common.align(bendyKneeInCtrl, bendyKneeInConstGrp)
    cmds.parent(bendyKneeInCtrl, bendyKneeInConstGrp)
    
    bendyKneeInManual = cmds.group(empty=1, name='%s_knee_bend_in_manual_targ' % side)
    common.align(bendyKneeInManual, bendyKneeInConstGrp)
    cmds.parent(bendyKneeInManual, resultChain[0])
    cmds.pointConstraint(bendyKneeCtrl, resultChain[0], bendyKneeInManual)
    cmds.pointConstraint(bendyKneeCtrl, bendyKneeInManual, e=1, w=2.0)
    
    bendyKneeInAuto = cmds.group(empty=1, name='%s_knee_bend_in_auto_targ' % side)
    common.align(bendyKneeInAuto, bendyKneeInConstGrp)
    cmds.parent(bendyKneeInAuto, bendyKneeCtrl)
    
    parentConstraint = cmds.parentConstraint(bendyKneeInManual, bendyKneeInAuto, bendyKneeInConstGrp)[0]
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.%sW1' % (parentConstraint, bendyKneeInAuto))
    rev = cmds.createNode('reverse', name='%s_knee_bend_auto_rev')
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.inputX' % rev)
    cmds.connectAttr('%s.outputX' % rev, '%s.%sW0' % (parentConstraint, bendyKneeInManual))
    
    # out
    bendyKneeOutConstGrp = cmds.group(empty=1, name='%s_knee_bend_out_const_grp' % side)
    common.align(bendyKneeOutConstGrp, resultChain[1])
    lowLegPoints = common.pointsAlongVector(resultChain[1], resultChain[2], divisions=3)
    cmds.setAttr('%s.t' % bendyKneeOutConstGrp, lowLegPoints[1][0], lowLegPoints[1][1], lowLegPoints[1][2])
    cmds.parent(bendyKneeOutConstGrp, bendGrp)
    
    bendyKneeOutCtrl = controls.squareCtrl(name='%s_knee_bend_out_ctrl' % side, axis='x', size=7.5)
    common.align(bendyKneeOutCtrl, bendyKneeOutConstGrp)
    cmds.parent(bendyKneeOutCtrl, bendyKneeOutConstGrp)
    
    bendyKneeOutManual = cmds.group(empty=1, name='%s_knee_bend_out_manual_targ' % side)
    common.align(bendyKneeOutManual, bendyKneeOutConstGrp)
    cmds.parent(bendyKneeOutManual, resultChain[1])
    cmds.pointConstraint(bendyKneeCtrl, resultChain[2], bendyKneeOutManual)
    cmds.pointConstraint(bendyKneeCtrl, bendyKneeOutManual, e=1, w=2.0)
    
    bendyKneeOutAuto = cmds.group(empty=1, name='%s_knee_bend_out_auto_targ' % side)
    common.align(bendyKneeOutAuto, bendyKneeOutConstGrp)
    cmds.parent(bendyKneeOutAuto, bendyKneeCtrl)
    
    parentConstraint = cmds.parentConstraint(bendyKneeOutManual, bendyKneeOutAuto, bendyKneeOutConstGrp)[0]
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.%sW1' % (parentConstraint, bendyKneeOutAuto))
    rev = cmds.createNode('reverse', name='%s_knee_bend_auto_rev')
    cmds.connectAttr('%s.auto_bend' % settingsCtrl, '%s.inputX' % rev)
    cmds.connectAttr('%s.outputX' % rev, '%s.%sW0' % (parentConstraint, bendyKneeOutManual))
    
    # Hip out
    bendyHipConstGrp = cmds.group(empty=1, name='%s_hip_bend_const_grp' % side)
    common.align(bendyHipConstGrp, resultChain[0])
    cmds.parent(bendyHipConstGrp, bendGrp)
    
    bendyHipCtrl = controls.squareCtrl(name='%s_hip_bend_ctrl' % side, axis='x', size=7.5)
    common.align(bendyHipCtrl, bendyHipConstGrp)
    cmds.parent(bendyHipCtrl, bendyHipConstGrp)
    cmds.pointConstraint(bendyKneeCtrl, resultChain[0], bendyHipConstGrp)
    cmds.pointConstraint(bendyKneeCtrl, bendyHipConstGrp, e=1, w=0.5)
    cmds.orientConstraint(resultChain[0], bendyHipConstGrp)
    
    # Ankle in
    bendyAnkleConstGrp = cmds.group(empty=1, name='%s_ankle_bend_const_grp' % side)
    common.align(bendyAnkleConstGrp, resultChain[1])
    cmds.parent(bendyAnkleConstGrp, bendGrp)
    
    bendyAnkleCtrl = controls.squareCtrl(name='%s_ankle_bend_ctrl' % side, axis='x', size=7.5)
    common.align(bendyAnkleCtrl, bendyAnkleConstGrp)
    cmds.parent(bendyAnkleCtrl, bendyAnkleConstGrp)
    cmds.pointConstraint(bendyKneeCtrl, resultChain[2], bendyAnkleConstGrp)
    cmds.pointConstraint(bendyKneeCtrl, bendyAnkleConstGrp, e=1, w=0.5)
    cmds.orientConstraint(resultChain[1], bendyAnkleConstGrp)
    
        
    ############################################################################################################################# Curve segments
    defJnts_grp = cmds.group(empty=1, name='%s_leg_defJnts_grp' % side)
    cmds.parent(defJnts_grp, root)
    
    # up leg
    upLegSeg = cmds.group(empty=1, name='%s_upLeg_segment_grp' % side)
    cmds.parent(upLegSeg, defJnts_grp)
    cmds.setAttr('%s.inheritsTransform' % upLegSeg, 0)
    
    crv = curve.curveBetweenNodes(start=upLeg, end=lowLeg, name='%s_upLeg' % side)
    cmds.parent(crv, const)
    
    mpNodes = curve.nodesAlongCurve(crv=crv, numNodes=twistJoints, name='%s_upLeg' % side, upNode=upLegNonRoll['nonRoll'])
    cmds.parent(mpNodes['grps'], upLegSeg)
    
    roll_uc = cmds.createNode('unitConversion', name='%s_upLeg_roll_uc' % side)
    cmds.setAttr('%s.conversionFactor' % roll_uc, 1.0)
    cmds.connectAttr('%s.rotateX' % lowLegNonRoll['info'], '%s.input' % roll_uc)
    
    kneeRoll_uc = cmds.createNode('unitConversion', name='%s_upLeg_kneeRoll_uc' % side)
    cmds.setAttr('%s.conversionFactor' % kneeRoll_uc, 1.0)
    cmds.connectAttr('%s.rotateX' % bendyKneeCtrl, '%s.input' % kneeRoll_uc)
    
    roll_pma = cmds.createNode('plusMinusAverage', name='%s_upLeg_roll_pma' % side)
    cmds.connectAttr('%s.output' % roll_uc, '%s.input1D[0]' % roll_pma)
    cmds.connectAttr('%s.output' % kneeRoll_uc, '%s.input1D[1]' % roll_pma)
    
    for i in range(len(mpNodes['mpNodes'])):
        # Create child Joint
        cmds.select(clear=1)
        j = cmds.joint(name='%s_upLeg_%s_defJnt' % (side, i))
        common.align(j, mpNodes['grps'][i])
        cmds.parent(j, mpNodes['grps'][i])
        
        totalRoll_uc = cmds.createNode('unitConversion', name='%s_upLeg_totalRoll_%s_uc' % (side, i+1))
        if side == 'lf':
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc,  (1.0 / (twistJoints-1) * i)*-1)
        else:
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc,  1.0 / (twistJoints-1) * i)
        cmds.connectAttr('%s.output1D' % roll_pma, '%s.input' % totalRoll_uc)
        cmds.connectAttr('%s.output' % totalRoll_uc, '%s.frontTwist' % mpNodes['mpNodes'][i])
    
    upLegCrvJnts = curve.bindCurve(crv=crv)
    cmds.parent(upLegCrvJnts[0], resultChain[0])
    cmds.parent(upLegCrvJnts[1], bendyHipCtrl)
    cmds.parent(upLegCrvJnts[2], bendyKneeInCtrl)
    cmds.parent(upLegCrvJnts[3], bendyKneeCtrl)
    
    # low leg
    lowLegSeg = cmds.group(empty=1, name='%s_lowLeg_segment_grp' % side)
    cmds.parent(lowLegSeg, defJnts_grp)
    cmds.setAttr('%s.inheritsTransform' % lowLegSeg, 0)
    
    crv = curve.curveBetweenNodes(start=lowLeg, end=ankle, name='%s_lowLeg' % side)
    cmds.parent(crv, const)
    
    mpNodes = curve.nodesAlongCurve(crv=crv, numNodes=twistJoints, name='%s_lowLeg' % side, upNode=resultChain[1])
    cmds.parent(mpNodes['grps'], lowLegSeg)
    
    for i in range(len(mpNodes['mpNodes'])):
        # Create child Joint
        cmds.select(clear=1)
        j = cmds.joint(name='%s_lowLeg_%s_defJnt' % (side, i))
        common.align(j, mpNodes['grps'][i])
        cmds.parent(j, mpNodes['grps'][i])
        
        roll_uc = cmds.createNode('unitConversion', name='%s_lowLeg_roll_%s_uc' % (side, i+1))
        cmds.setAttr('%s.conversionFactor' % roll_uc, 1.0 / (twistJoints-1) * i)
        cmds.connectAttr('%s.rotateX' % ankleNonRoll['info'], '%s.input' % roll_uc)
        
        kneeRoll_uc = cmds.createNode('unitConversion', name='%s_lowLeg_kneeRoll_%s_uc' % (side, i+1))
        cmds.setAttr('%s.conversionFactor' % kneeRoll_uc, 1.0 - (1.0 / (twistJoints-1) * i))
        cmds.connectAttr('%s.rotateX' % bendyKneeCtrl, '%s.input' % kneeRoll_uc)
        
        roll_pma = cmds.createNode('plusMinusAverage', name='%s_lowLeg_roll_%s_pma' % (side, i+1))
        cmds.connectAttr('%s.output' % roll_uc, '%s.input1D[0]' % roll_pma)
        cmds.connectAttr('%s.output' % kneeRoll_uc, '%s.input1D[1]' % roll_pma)
        
        totalRoll_uc = cmds.createNode('unitConversion', name='%s_lowLeg_totalRoll_%s_uc' % (side, i+1))
        if side == 'lf':
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc, -1.0)
        else:
            cmds.setAttr('%s.conversionFactor' % totalRoll_uc, 1.0)
        cmds.connectAttr('%s.output1D' % roll_pma, '%s.input' % totalRoll_uc)
        cmds.connectAttr('%s.output' % totalRoll_uc, '%s.frontTwist' % mpNodes['mpNodes'][i])
    
    lowLegCrvJnts = curve.bindCurve(crv=crv)
    cmds.parent(lowLegCrvJnts[0], bendyKneeCtrl)
    cmds.parent(lowLegCrvJnts[1], bendyKneeOutCtrl)
    cmds.parent(lowLegCrvJnts[2], bendyAnkleCtrl)
    cmds.parent(lowLegCrvJnts[3], resultChain[2])
    
    ############################################################################################################################################## CLEANUP
    if cleanup:
        cmds.setAttr('%s.visibility' % const, 0)
        common.attrCtrl(lock=True, keyable=False, channelBox=False, nodeList=[const, bendyKneeCtrl], attrList=['visibility'])
        
        common.attrCtrl(lock=True, keyable=False, channelBox=False,
                        nodeList=[fkUpLegCtrl, fkLowLegCtrl, fkFootCtrl],
                        attrList=['visibility', 'tx', 'ty', 'tz', 'sx', 'sy', 'sz'])
        
        common.attrCtrl(lock=True, keyable=False, channelBox=False,
                        nodeList=[ikFootCtrl,],
                        attrList=['visibility', 'sx', 'sy', 'sz'])
        
        common.attrCtrl(lock=True, keyable=False, channelBox=False,
                        nodeList=[ikKneeCtrl, bendyHipCtrl, bendyKneeInCtrl, bendyKneeOutCtrl, bendyAnkleCtrl],
                        attrList=['visibility', 'sx', 'sy', 'sz'])
        
    ############################################################################################################################################## RETURN
    returnDict={
                'upLeg_fk_ctrl':fkUpLegCtrl,
                'lowLeg_fk_ctrl':fkLowLegCtrl,
                'foot_fk_ctrl':fkFootCtrl,
                'foot_ik_ctrl':ikFootCtrl,
                'knee_ik_ctrl': ikKneeCtrl,
                'settings':settingsCtrl,
                'knee_bend_ctrl':bendyKneeCtrl,
                'hip_bend_ctrl':bendyHipCtrl,
                'knee_in_bend_ctrl':bendyKneeInCtrl,
                'knee_out_bend_ctrl':bendyKneeInCtrl,
                'root':root,
                'const':const
                }
    
    return returnDict
        
        
        
        
        
        
        
        
        
        