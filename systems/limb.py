import pymel.core as pmc
import maya.cmds as cmds
from rooftops.core import common
from rooftops.systems import curve, controls, measure, nonRoll

legNames=['upper', 'lower', 'ankle', 'end']
armNames=['upper', 'lower', 'wrist', 'end']

def tripleChain(top=None, mid=None, bot=None, end=None, prefix='', settingsCtrl=None, globalScaleAttr=None, nameList=legNames):
    '''
    makes an fk, ik and result chain based on the supplied 4 joint hierarchy
    '''

    #Validation
    if not top or not mid or not bot or not end:
        if len(pmc.selected()) == 4:
            top = pmc.selected()[0]
            mid = pmc.selected()[1]
            bot = pmc.selected()[2]
            end = pmc.selected()[3]
        else:
            return common.showDialog('Argument Error', 'Please supply 4 hierarchical joints')

    ##################################################################################################################################################
    # Base groups
    ##################################################################################################################################################
    # Root group
    root = pmc.group(empty=1, name='%s_grp' % prefix)
    if not globalScaleAttr:
        globalScaleAttr = root.sx

    #Constrain group which is aligned to the first joint and can be used to attach the limb to a shoulder or hip
    const = pmc.group(empty=1, name='%s_const_grp' % prefix)
    common.align(const.nodeName(), top.nodeName())
    const.setParent(root)

    def _duplicateChain(chainType):
        dupes = cmds.duplicate(top.nodeName(), rc=1)
        print dupes
        dupes = pmc.ls(dupes)
        for d in range(4):
            dupes[d].rename('%s_%s_%s_jnt' % (prefix, nameList[d], chainType))
        return dupes

    resultChain = _duplicateChain('result')
    resultChain[0].setParent(const)
    fkChain = _duplicateChain('fk')
    fkChain[0].setParent(const)
    ikChain = _duplicateChain('ik')
    ikChain[0].setParent(const)

    ##################################################################################################################################################
    # SETTINGS & ATTRS
    ##################################################################################################################################################
    if not settingsCtrl:
        settingsCtrl = controls.crossCtrl(name='%s_settings_ctrl' % prefix)
        common.align(settingsCtrl.nodeName(), const.nodeName())
        settingsCtrl.setParent(root)
        # ik / fk attr
        pmc.addAttr(settingsCtrl, longName='state', at='float', minValue=0.0, maxValue=1.0, keyable=True, hidden=0)
        stateRev = pmc.createNode('reverse', name='%s_state_rev' % prefix)
        settingsCtrl.state.connect(stateRev.inputX)
        # bendy ctrls switch
        pmc.addAttr( settingsCtrl, longName='bendy_ctrls', at='enum', enumName='hide:show', keyable=True )
        pmc.parentConstraint(resultChain[2], settingsCtrl)


    ##################################################################################################################################################
    # FK CTRLS
    ##################################################################################################################################################
    fkGrp = pmc.group(empty=1, name='%s_fk_grp' % prefix)
    fkGrp.setParent(const)
    settingsCtrl.state.connect(fkGrp.visibility)

    # fk top ctrl
    fkTopCtrl = controls.circleBumpCtrl(name='%s_%s_fk_ctrl' % (prefix, nameList[0]), axis='x', radius=10)
    common.align(fkTopCtrl.nodeName(), fkChain[0].nodeName())
    fkTopCtrl.setParent(fkGrp)
    common.insertGroup(fkTopCtrl.nodeName())

    # fk mid ctrl
    fkMidCtrl = controls.circleBumpCtrl(name='%s_%s_fk_ctrl' % (prefix, nameList[1]), axis='x', radius=10)
    common.align(fkMidCtrl.nodeName(), fkChain[1].nodeName())
    fkMidCtrl.setParent(fkTopCtrl)
    common.insertGroup(fkMidCtrl.nodeName())

    # fk bot ctrl
    fkBotCtrl = controls.circleBumpCtrl(name='%s_%s_fk_ctrl' % (prefix, nameList[2]), axis='x', radius=10)
    common.align(fkBotCtrl.nodeName(), fkChain[2].nodeName())
    fkBotCtrl.setParent(fkMidCtrl)
    common.insertGroup(fkBotCtrl.nodeName())

    pmc.parentConstraint(fkTopCtrl, fkChain[0])
    pmc.parentConstraint(fkMidCtrl, fkChain[1])
    pmc.parentConstraint(fkBotCtrl, fkChain[2])

    # add extend attrs
    for ctrl in [fkMidCtrl, fkBotCtrl]:
        pmc.addAttr( ctrl, longName='extend', at='double', keyable=True )
        boneLen = ctrl.getParent().tx.get()
        if boneLen > 0.0:
            extend_pma = common.add([boneLen, ctrl.extend], name='%s_extend_pma' % ctrl.nodeName())
        else:
            extend_pma = common.minus([boneLen, ctrl.extend], name='%s_extend_pma' % ctrl.nodeName())
        extend_pma.output1D.connect(ctrl.getParent().tx)

    ##################################################################################################################################################
    # IK BUSINESS
    ##################################################################################################################################################
    ikGrp = pmc.group(empty=1, name='%s_ik_grp' % prefix)
    ikGrp.setParent(root)
    stateRev.outputX.connect(ikGrp.visibility)

    # IK ctrl
    ikCtrl = controls.boxCtrl(name='%s_ik_ctrl' % prefix, size=10)
    common.align(ikCtrl.nodeName(), resultChain[2].nodeName(), orient=0)
    ikCtrl.setParent(ikGrp)
    common.insertGroup(ikCtrl.nodeName())

    pmc.addAttr( ikCtrl, longName='stretch', at='double', minValue=0, maxValue=1, defaultValue=0, keyable=True )
    pmc.addAttr( ikCtrl, longName='extend', at='double', keyable=True )
    pmc.addAttr( ikCtrl, longName='soft', at='double', minValue=0, defaultValue=0, keyable=True )

    # Set up ik / fk blending
    for i in range(4):
        common.blendAttrs(targ1=ikChain[i].nodeName(), targ2=fkChain[i].nodeName(), driven=resultChain[i].nodeName(), blendAttr='%s.state' % settingsCtrl.nodeName())

    # Soft non-stretchy IK stuff
    softBlendLoc = pmc.spaceLocator(name='%s_softBlendLoc' % prefix)
    common.align(softBlendLoc.nodeName(), ikCtrl.nodeName())
    softBlendLoc.setParent(ikGrp)

    aimLoc = pmc.spaceLocator(name='%s_softIkAimLoc' % prefix)
    common.align(aimLoc.nodeName(), const.nodeName())
    aimLoc.setParent(const)
    pmc.aimConstraint(ikCtrl, aimLoc)

    wristLoc = pmc.spaceLocator(name='%s_wristLoc' % prefix)
    common.align(wristLoc.nodeName(), ikCtrl.nodeName())
    wristLoc.setParent(aimLoc)

    ctrlDist = common.distanceBetweenNodes(aimLoc, ikCtrl, name='%s_ctrlDist' % prefix)
    softDist = common.distanceBetweenNodes(wristLoc, softBlendLoc, name='%s_softDist' % prefix)
    stretchDist = common.distanceBetweenNodes(aimLoc, softBlendLoc, name='%s_stretchDist' % prefix)

    chainLen = abs(ikChain[1].tx.get() + ikChain[2].tx.get())

    chainLenMinusSoft = common.minus([chainLen, ikCtrl.soft], name='%s_chainLenMinusSoft_pma' % prefix)
    print(chainLenMinusSoft)

    isStretchedCond = pmc.createNode('condition', name='%s_isStretched_cond' % prefix)
    isStretchedCond.operation.set(2)
    ctrlDist.distance.connect(isStretchedCond.firstTerm)
    chainLenMinusSoft.output1D.connect(isStretchedCond.secondTerm)
    ctrlDist.distance.connect(isStretchedCond.colorIfFalseR)

    isSoftCond = pmc.createNode('condition', name='%s_isSoft_cond' % prefix)
    isSoftCond.operation.set(2)
    ikCtrl.soft.connect(isSoftCond.firstTerm)
    isSoftCond.colorIfFalseR.set(chainLen)

    ctrlDistMinusSoftChain = common.minus([ctrlDist.distance, chainLenMinusSoft.output1D], name='%s_ctrlDistMinusSoftChain_pma' % prefix)

    divideBySoft = common.divide(ctrlDistMinusSoftChain.output1D, ikCtrl.soft, name='%s_divideBySoft_md' % prefix)

    invert = common.multiply(divideBySoft.outputX, -1, name='%s_invertSoft_md' % prefix)

    exp = common.pow(2.718282, invert.outputX, name='%s_exponential_md' % prefix)

    multiplyBySoft = common.multiply(exp.outputX, ikCtrl.soft, name='%s_multiplyBySoft_md' % prefix)

    minusFromChainLen = common.minus([chainLen, multiplyBySoft.outputX], name='%s_minusFromChainLen_md' % prefix)

    minusFromChainLen.output1D.connect(isSoftCond.colorIfTrueR)

    isSoftCond.outColorR.connect(isStretchedCond.colorIfTrueR)

    isStretchedCond.outColorR.connect(wristLoc.tx)

    # stretchy soft IK stuff
    pc = pmc.pointConstraint(wristLoc, ikCtrl, softBlendLoc)
    stretchRev = pmc.createNode('reverse', name='%s_stretch_rev' % prefix)
    ikCtrl.stretch.connect(stretchRev.inputX)
    stretchRev.outputX.connect('%s.%sW0' % (pc.nodeName(), wristLoc.nodeName()))
    ikCtrl.stretch.connect('%s.%sW1' % (pc.nodeName(), ikCtrl.nodeName()))

    globalScaleDiv = common.divide(1.0, globalScaleAttr, name='%s_globalScaleDiv_md' % prefix)

    scaledSoftDist = common.multiply(globalScaleDiv.outputX, softDist.distance, name='%s_scaledSoftDist_md' % prefix)

    # Stretchy Mid
    midLen = common.multiply((mid.tx.get() / chainLen), scaledSoftDist.outputX, name='%s_midLen_md' % prefix)

    stretchMidLen = common.multiply(ikCtrl.stretch, midLen.outputX, name='%s_stretchMidLen_md' % prefix)

    stretchMidLenPlusBoneLen = common.add([mid.tx.get(), stretchMidLen.outputX], name='%s_stretchMidLenPlusBoneLen_pma' % prefix)

    stretchMidLenPlusBoneLen.output1D.connect(ikChain[1].tx)

    # Stretchy Bot
    botLen = common.multiply((bot.tx.get() / chainLen), scaledSoftDist.outputX, name='%s_botLen_md' % prefix)

    stretchBotLen = common.multiply(ikCtrl.stretch, botLen.outputX, name='%s_stretchBotLen_md' % prefix)

    stretchBotLenPlusBoneLen = common.add([bot.tx.get(), stretchBotLen.outputX], name='%s_stretchBotLenPlusBoneLen_pma' % prefix)

    stretchBotLenPlusBoneLen.output1D.connect(ikChain[2].tx)


    # IK Solvers
    ikHandleGrp = pmc.group(empty=1, name='%s_ikHandle_grp' % prefix)
    common.align(ikHandleGrp.nodeName(), ikCtrl.nodeName())
    ikHandleGrp.setParent(softBlendLoc)
    pmc.orientConstraint(ikCtrl, ikHandleGrp, mo=1)

    ikHandle = pmc.ikHandle(solver='ikRPsolver', name='%s_ikHandle' % prefix, startJoint=ikChain[0], endEffector=ikChain[2])[0]
    common.align(ikHandle.nodeName(), resultChain[2].nodeName())
    ikHandle.setParent(ikHandleGrp)

    endIkHandle = pmc.ikHandle(solver='ikSCsolver', name='%s_end_ikHandle' % prefix, startJoint=ikChain[2], endEffector=ikChain[3])[0]
    common.align(endIkHandle.nodeName(), resultChain[3].nodeName())
    endIkHandle.rx.set(0)
    endIkHandle.setParent(ikHandleGrp)

    ##################################################################################################################################################
    # NON ROLLS
    ##################################################################################################################################################
    topNonRoll = nonRoll.build(joint=resultChain[0].nodeName(), name='%s_top' % prefix)
    cmds.parent(topNonRoll['main_grp'], const.nodeName())

    midNonRoll = nonRoll.build(joint=resultChain[1].nodeName(), name='%s_mid' % prefix)
    cmds.parent(midNonRoll['main_grp'], topNonRoll['nonRoll'])

    botNonRoll = nonRoll.build(joint=resultChain[2].nodeName(), name='%s_bot' % prefix)
    cmds.parent(botNonRoll['main_grp'], resultChain[1].nodeName())