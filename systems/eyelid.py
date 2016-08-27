import pymel.core as pmc
import rooftops.core.common as common
import rooftops.systems.curve as curve

def build(crv, name=''):
    '''
    creates a Marco Giordano style eyelid rig

    '''
    params = [curve.getClosestPointOnCurve(crv=crv, point = pmc.pointPosition(cv)) for cv in crv.cv[:]]

    mainGrp = pmc.group(empty=1, name='%s_grp' % name)
    baseGrp = pmc.group(empty=1, name='%s_base_grp' % name)
    baseGrp.setParent(mainGrp)

    mps = curve.nodesAlongCurve(crv=crv.name(), numNodes=len(params), name=name)

    for index in range(len(params)):
        mp = common.getPyNode(mps['mpNodes'][index])
        mp.uValue.set(params[index])
        mp.fractionMode.set(0)

        grp = common.getPyNode(mps['grps'][index])

        aimGrp = pmc.group(empty=1, name='%s_%s_aim_grp' % (name, str(index)))
        aimGrp.setParent(baseGrp)
        con = pmc.aimConstraint(grp, aimGrp, mo=0, wut=2, wuo=baseGrp.name())

        pmc.select(aimGrp, r=1)
        j = pmc.joint(name='%s_%s_jnt' % (name, str(index)))
        j.tx.set(10)

build(crv=common.getPyNode('lid_top_lo_crvShape'))