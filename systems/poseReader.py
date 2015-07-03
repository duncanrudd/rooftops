import maya.cmds as cmds
import maya.OpenMaya as om
from ROOFTOPS.core import common

class PoseReader(object):
    '''
    Class which generates a base node that reads the angle between two vectors
    Targets can then be added to it with attributes for falloff
    
    '''
    def __init__(self, target, name='', axis='x'):
        self.name = name
        self.axis = axis
        self.target = target
        
        self.build()
        
    def build(self):
        self.main_grp = cmds.group(empty=1, name=(self.name + '_base_grp'))
        common.align(self.main_grp, self.target)
        self.main_jnt = cmds.joint(name=(self.main_grp.replace('grp', 'jnt')))
        self.orient_jnt = cmds.joint(name=(self.main_jnt.replace('base', 'orient')))
        cmds.select(self.main_jnt)
        self.reader_jnt = cmds.joint(name=(self.main_jnt.replace('base', 'reader')))
        cmds.setAttr(self.reader_jnt + '.t' + self.axis, 1.0)
        cmds.parentConstraint(self.orient_jnt, self.reader_jnt, mo=1)
        cmds.orientConstraint(self.target, self.orient_jnt)
        
    def add_target(self, name):
        cmds.select(self.main_jnt)
        jnt = cmds.joint(name=self.name + '_' + name + '_target_jnt')
        cmds.setAttr(jnt + '.t' + self.axis, 1.0)
        cmds.addAttr(jnt, ln='cone_angle', at='double', keyable=1, maxValue=360, minValue=0)
        cmds.addAttr(jnt, ln='pose_weight', at='double')
        
        norm_vp = cmds.createNode('vectorProduct', name = self.name + '_' + name + 'normalize_vp')
        cmds.connectAttr(jnt + '.t', norm_vp + '.input1')
        cmds.setAttr(norm_vp + '.normalizeOutput', 1)
        cmds.setAttr(norm_vp + '.operation', 0)
        
        dot_vp = cmds.createNode('vectorProduct', name = self.name + '_' + name + 'dot_vp')
        cmds.connectAttr(norm_vp + '.output', dot_vp + '.input1')
        cmds.connectAttr(self.reader_jnt + '.t', dot_vp + '.input2')
        cmds.setAttr(dot_vp + '.normalizeOutput', 1)
        
        angle_rv = cmds.createNode('remapValue', name= self.name + '_' + name + '_angle_rv')
        cmds.connectAttr(jnt + '.cone_angle', angle_rv + '.inputValue')
        cmds.setAttr(angle_rv + '.value[0].value_FloatValue', 1)
        cmds.setAttr(angle_rv + '.value[1].value_FloatValue', -1)
        cmds.setAttr(angle_rv + '.inputMax', 360.0)
        
        rv = cmds.createNode('remapValue', name= self.name + '_' + name + '_rv')
        #cmds.connectAttr(jnt + '.cone_angle', rv + '.value[0].value_Position')
        cmds.connectAttr(angle_rv + '.outValue', rv + '.value[0].value_Position')
        cmds.connectAttr(dot_vp + '.outputX', rv + '.inputValue')
        cmds.connectAttr(rv + '.outValue', jnt + '.pose_weight')