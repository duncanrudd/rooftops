import pymel.core as pmc
import rooftops.core.common as common
reload(common)

def build(name='', side='rt', settingsNode=''):
    main_grp = pmc.group(empty=1, name=name + '_grp')

    const_grp = pmc.group(empty=1, name=name + '_const_grp')
    const_grp.setParent(main_grp)
    const_grp.tz.set(-4)

    outer_grp = pmc.group(empty=1, name=name + '_outer_grp')
    outer_grp.setParent(const_grp)
    outer_loc = pmc.spaceLocator(name=name + '_outer_loc')
    outer_loc.setParent(outer_grp)
    if side == 'lf':
        outer_grp.tx.set(2)
    else:
        outer_grp.tx.set(-2)

    inner_grp = pmc.group(empty=1, name=name + '_inner_grp')
    inner_grp.setParent(outer_loc)
    inner_loc = pmc.spaceLocator(name=name + '_inner_loc')
    inner_loc.setParent(inner_grp)
    inner_grp.tx.set(outer_grp.tx.get() * -2)

    heel_grp = pmc.group(empty=1, name=name + '_heel_grp')
    heel_grp.setParent(inner_loc)
    heel_loc = pmc.spaceLocator(name=name + '_heel_loc')
    heel_loc.setParent(heel_grp)
    heel_grp.tz.set(-4)
    heel_grp.tx.set(inner_grp.tx.get() * -.5)

    toe_loc = pmc.spaceLocator(name=name + '_toe_loc')
    toe_loc.setParent(heel_loc)
    toe_loc.tz.set(8)

    ballPivot_loc = pmc.spaceLocator(name=name + '_ballPivot_loc')
    ballPivot_loc.setParent(toe_loc)
    ballPivot_loc.tz.set(-2)

    toeFlex_loc = pmc.spaceLocator(name=name + '_toeFlex_loc')
    toeFlex_loc.setParent(ballPivot_loc)
    toeFlex_loc.tz.set(0)

    ball_loc = pmc.spaceLocator(name=name + '_ball_loc')
    ball_loc.setParent(ballPivot_loc)
    ball_loc.tz.set(0)

    if not settingsNode:
        settingsNode = main_grp

    attrs = ['rock_ball', 'rock_toe', 'rock_side', 'pivot_ball', 'pivot_toe', 'flex_toe', 'lean']

    for attr in attrs:
        pmc.addAttr(settingsNode, ln=attr, keyable=1, hidden=0)

    settingsNode.rock_ball.connect(ball_loc.rx)
    settingsNode.rock_toe.connect(toe_loc.rx)
    settingsNode.flex_toe.connect(toeFlex_loc.rx)


    if side == 'rt':
        settingsNode.rock_side.connect(outer_loc.rz)
        settingsNode.rock_side.connect(inner_loc.rz)
        pmc.transformLimits(outer_loc, rz=(0, 45), erz=(1, 0))
        pmc.transformLimits(inner_loc, rz=(-45, 0), erz=(0, 1))
        settingsNode.pivot_ball.connect(ballPivot_loc.ry)
        settingsNode.pivot_toe.connect(toe_loc.ry)
        settingsNode.lean.connect(ball_loc.rz)
    else:
        uc = common.convert(settingsNode.rock_side, -0.018, name + '_rock_side_uc')
        uc.output.connect(outer_loc.rz)
        uc.output.connect(inner_loc.rz)
        pmc.transformLimits(outer_loc, rz=(-45, 0), erz=(0, 1))
        pmc.transformLimits(inner_loc, rz=(0, 45), erz=(1, 0))
        uc = common.convert(settingsNode.pivot_ball, -0.018, name + '_pivot_ball_uc')
        uc.output.connect(ballPivot_loc.ry)
        uc = common.convert(settingsNode.pivot_toe, -0.018, name + '_pivot_toe_uc')
        uc.output.connect(toe_loc.ry)
        uc = common.convert(settingsNode.lean, -0.018, name + '_lean_uc')
        uc.output.connect(ball_loc.rz)


