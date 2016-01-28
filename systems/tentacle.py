import rooftops.systems.curve as rt_curve
import rooftops.systems.controls as rt_controls
import maya.cmds as cmds
from rooftops.core import common

class Tentacle(object):
    def __init__(self, name='', numCtrls=17):
        super(Tentacle, self).__init__()
        self.name = name
        self.numCtrls = numCtrls
        self.build()

    def build(self):
        self.tangentCrv = rt_curve.TangentCurve(points=cmds.ls(sl=1), name=self.name)
        self.main_grp = cmds.group(empty=1, name='%s_grp' % self.name)
        cmds.parent(self.tangentCrv.dnt_grp, self.main_grp)

        # Ctrls
        self.ctrls = []
        for loc in self.tangentCrv.cv_locs:
            ctrl = rt_controls.circleBumpCtrl(radius=10, name=loc.replace('loc', 'ctrl'), axis='y')
            common.align(ctrl, loc, orient=0)
            cmds.parent(loc, ctrl)
            cmds.parent(ctrl, self.main_grp)
            common.insertGroup(ctrl)
            cmds.addAttr(ctrl, ln='tangentWeight', at="float", minValue=0.0, maxValue=1.0, keyable=1, hidden=0, defaultValue=0.25 )
            cmds.connectAttr('%s.tangentWeight' % ctrl, '%s.tangentWeight' % loc)
            self.ctrls.append(ctrl)

        # set up stretch blending
        cmds.addAttr(self.ctrls[-1], ln='stretch', at="float", minValue=0.0, maxValue=1.0, keyable=1, hidden=0, defaultValue=1.0 )
        cmds.addAttr(self.ctrls[-1], ln='stretchValue', at="float", keyable=0, hidden=0)
        info = cmds.createNode('curveInfo', name='%s_crvInfo' % self.name)
        cmds.connectAttr('%s.worldSpace[0]' % self.tangentCrv.crv, '%s.inputCurve' % info)
        stretch_md = cmds.createNode('multiplyDivide', name='%s_stretch_md' % self.name)
        cmds.connectAttr('%s.arcLength' % info, '%s.input2X' % stretch_md)
        cmds.setAttr('%s.input1X' % stretch_md, cmds.getAttr('%s.input2X' % stretch_md))
        cmds.setAttr('%s.operation' % stretch_md, 2)
        cmds.connectAttr('%s.outputX' % stretch_md, '%s.stretchValue' % self.ctrls[-1])



        # Nodes along curve
        self.pathNodes = rt_curve.nodesAlongCurve(crv=self.tangentCrv.crv, numNodes=self.numCtrls, name=self.name)
        for i in range(len(self.pathNodes['mpNodes'])):
            mp = self.pathNodes['mpNodes'][i]
            if i == 0:
                cmds.pathAnimation(mp, e=1, wut='objectrotation', wuo=self.ctrls[0])
            else:
                cmds.pathAnimation(mp, e=1, wut='objectrotation', wuo=self.pathNodes['grps'][i-1])

                # Add stretching functionality
                blend = cmds.createNode('blendTwoAttr', name=mp.replace('mp', 'stretch_blend'))
                cmds.connectAttr('%s.stretch' % self.ctrls[-1], '%s.attributesBlender' % blend)
                uc = cmds.createNode('unitConversion', name=mp.replace('mp', 'stretch_uc'))
                cmds.connectAttr('%s.stretchValue' % self.ctrls[-1], '%s.input' % uc)
                cmds.setAttr('%s.conversionFactor' % uc, cmds.getAttr('%s.uValue' % mp))
                cmds.connectAttr('%s.output' % uc, '%s.input[0]' % blend)
                cmds.setAttr('%s.input[1]' % blend, cmds.getAttr('%s.uValue' % mp))
                cmds.connectAttr('%s.output' % blend, '%s.uValue' % mp)
            cmds.parent(self.pathNodes['grps'][i], self.tangentCrv.dnt_grp)






