import maya.cmds as cmds
from rooftops.core import common
from rooftops.systems import rivet

def build(numBindJoints=6, numSpans=None, name='', numSkinJoints=3, width=None):
    '''
    builds a nurbs ribbon
    If width is not specified, width will be set to numBindJoints
    If numSpans is not specified, it will be set to numBindJoints
    
    '''
    if not width:
        width = numBindJoints
    if not numSpans:
        numSpans = numBindJoints
    
    main_grp = cmds.group(empty=1, name=(name + '_grp'))
    plane = cmds.nurbsPlane(axis=(0, 1, 0), ch=0, lengthRatio=(1.0 / width), w=width, u=numSpans, name=(name + '_nurbsPlane'))[0]
    cmds.parent(plane, main_grp)
    
    # Creat Skin joints
    skinJoints = []
    skinJointPositions = common.pointsAlongVector( start=[width*.5, 0, 0], end=[width*-.5, 0, 0], divisions=(numSkinJoints-1) )
    for index in range(len(skinJointPositions)):
        cmds.select(main_grp)
        j = cmds.joint(position = skinJointPositions[index], name=(name + '_' + str(index) + '_jnt'))
        skinJoints.append(j)
        
    # Add skinning to ribbon
    cmds.skinCluster(skinJoints, plane, tsb=1, name=(plane + '_skinCluster'))
    cmds.setAttr(plane+'.inheritsTransform', 0)
    
    # Add follicles
    for index in range(numBindJoints):
        f = rivet.build( mesh=plane, paramU=(1.0 / (numBindJoints-1) * index), paramV=0.5, name=(name + '_' + str(index)))
        cmds.parent(f, main_grp)
        j = cmds.joint(name=(name + '_' + str(index) + '_bnd'))
    