import pymel.core as pmc
from rooftops.systems import curve, controls
import rooftops.core.common as common

def buildSpine(start, end, numJoints=10, name=''):
    # base groups
    main_grp = pmc.group(empty=1, name='%s_grp' % name)
    const_grp = pmc.group(empty=1, name='%s_const_grp' % name)
    common.align(const_grp.nodeName(), start, orient=0)

    # Create curve
    crv = curve.curveBetweenNodes(start, end, name=name)
    crvJoints = curve.bindCurve(crv)

    # controls
    # hips
    hip_ctrl = controls.circleBumpCtrl(name='%s_hips_ctrl' % name, axis='y')
    common.align(hip_ctrl.nodeName(), crvJoints[1])
    hip_ctrl.setParent(const_grp)
    pmc.parent(crvJoints[0], hip_ctrl)
    hip_tan_grp = common.insertGroup(crvJoints[0])
    hip_tan_grp = pmc.rename(hip_tan_grp, '%s_hips_tangent_grp' % name)
    pmc.parent(crvJoints[1], hip_tan_grp)
    pmc.parent(hip_tan_grp, hip_ctrl)
    common.insertGroup(hip_ctrl.nodeName())

    # chest
    chest_ctrl = controls.circleBumpCtrl(name='%s_chest_ctrl' % name, axis='y')
    common.align(chest_ctrl.nodeName(), crvJoints[2])
    chest_ctrl.setParent(const_grp)
    pmc.parent(crvJoints[3], chest_ctrl)
    chest_tan_grp = common.insertGroup(crvJoints[3])
    chest_tan_grp = pmc.rename(chest_tan_grp, '%s_chest_tangent_grp' % name)
    pmc.parent(crvJoints[2], chest_tan_grp)
    pmc.parent(chest_tan_grp, chest_ctrl)
    common.insertGroup(chest_ctrl.nodeName())

    # curve tangent stuff
    # crvInfo
    crvInfo = pmc.createNode('curveInfo', name='%s_crvInfo' % name)
    crvShape = common.getShape(crv)
    crvShape.worldSpace[0].connect(crvInfo.inputCurve)

    # distance
    ctrlDist = common.distanceBetweenNodes(hip_ctrl, chest_ctrl, name='%s_dist' % name)
    distMD = common.divide(ctrlDist.distance, ctrlDist.distance.get(), name='%s_ctrlDist_md')
    ctrlDistMult = common.pow(distMD.outputX, 0.5, name='%s_ctrlDistMult_md')

    # angle
    hipVp = pmc.createNode('vectorProduct', name='%s_hipAngle_vp' % name)
    hipVp.operation.set(3)
    hip_ctrl.worldMatrix[0].connect(hipVp.matrix)
    hipVp.input1X.set(0.0)
    hipVp.input1Y.set(1.0)
    hipVp.input1Z.set(0.0)

    chestVp = pmc.createNode('vectorProduct', name='%s_chestAngle_vp' % name)
    chestVp.operation.set(3)
    chest_ctrl.worldMatrix[0].connect(chestVp.matrix)
    chestVp.input1X.set(0.0)
    chestVp.input1Y.set(1.0)
    chestVp.input1Z.set(0.0)

    dotVp = pmc.createNode('vectorProduct', name='%s_angle' % name)
    hipVp.output.connect(dotVp.input1)
    chestVp.output.connect(dotVp.input2)
    dotVp.normalizeOutput.set(1)

    dotPMA = common.add([dotVp.outputX, 1.0], name='%_dotPlusOne_pma')
    dotMult = common.multiply(dotPMA.output1D, 0.25, name='%s_dot_md')
    dotRev = pmc.createNode('reverse', name='%s_dot_rev' % name)
    dotMult.outputX.connect(dotRev.inputX)

    tanPMA = common.add([dotRev.outputX, ctrlDistMult.outputX], name='%s_tangent_pma')

    tanPMA.output1D.connect('%s.sx' % hip_tan_grp)
    tanPMA.output1D.connect('%s.sy' % hip_tan_grp)
    tanPMA.output1D.connect('%s.sz' % hip_tan_grp)
    tanPMA.output1D.connect('%s.sx' % chest_tan_grp)
    tanPMA.output1D.connect('%s.sy' % chest_tan_grp)
    tanPMA.output1D.connect('%s.sz' % chest_tan_grp)


    # stretch
    stretchMD = common.divide(crvInfo.arcLength, crvInfo.arcLength.get(), name='%s_stretch_md' % name)

    # pathNodes
    mps = curve.nodesAlongCurve(crv=crv, numNodes=numJoints, name=name, followAxis='y', upAxis='z', upNode=hip_ctrl.nodeName(), upVec='z')