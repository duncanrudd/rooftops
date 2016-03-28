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

    def _duplicateChain(chainType):
        dupes = cmds.duplicate(top.nodeName(), rc=1)
        print dupes
        dupes = pmc.ls(dupes)
        for d in range(4):
            dupes[d].rename('%s_%s_%s_jnt' % (prefix, nameList[d], chainType))
        return dupes

    resultChain = _duplicateChain('result')
    fkChain = _duplicateChain('fk')
    ikChain = _duplicateChain('ik')

    ##################################################################################################################################################
    # Base groups
    ##################################################################################################################################################
    # Root group
    root = pmc.group(empty=1, name='%s_grp' % prefix)

    #Constrain group which is aligned to the first joint and can be used to attach the limb to a shoulder or hip
    const = pmc.group(empty=1, name='%s_const_grp' % prefix)
    common.align(const.nodeName(), top.nodeName())
    const.setParent(root)

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

    ##################################################################################################################################################
    # IK BUSINESS
    ##################################################################################################################################################
    # IK Solvers
    ikHandle = pmc.ikHandle(solver='ikRPsolver', name='%s_ikHandle' % prefix, startJoint=ikChain[0], endEffector=ikChain[2])[0]
    common.align(ikHandle.nodeName(), resultChain[2].nodeName())

    endIkHandle = pmc.ikHandle(solver='ikSCsolver', name='%s_end_ikHandle' % prefix, startJoint=ikChain[2], endEffector=ikChain[3])[0]
    common.align(endIkHandle.nodeName(), resultChain[3].nodeName())
    endIkHandle.rx.set(0)

    # Set up ik / fk blending
    for i in range(4):
        common.blendAttrs(targ1=ikChain[i].nodeName(), targ2=fkChain[i].nodeName(), driven=resultChain[i].nodeName(), blendAttr='%s.state' % settingsCtrl.nodeName())

