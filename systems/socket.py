'''
Create space switching constraints on a node

'''
import maya.cmds as cmds
from rooftops.core.common import align


def build(node=None, targetList=[], targetNames=[], settingsNode=None, point=1, orient=1, parent=0,  name=''):
    # Argument validation
    if not node or not targetList:
        sel = cmds.ls(sl=1)
        if len(sel) > 1:
            node = sel[0]
            targetList = [s for s in sel[1:]]
        else:
            return 'Please supply or select node and targetList'
    if type(targetList) == type(''):
        targetList = [targetList]
    if not settingsNode:
        settingsNode = node
    if not targetNames:
        targetNames = [t for t in targetList]

    # main group
    main_grp = cmds.group(empty=1, name=(name + '_socket_grp'))

    #constrained group
    const_grp = cmds.group(empty=1, name=(name +'_const_grp'))
    align(const_grp, node)
    cmds.parent(const_grp, main_grp)
    cmds.parentConstraint(const_grp, node)

    #targets
    targets = []
    for t in range(len(targetList)):
        targ = cmds.duplicate(const_grp)
        targ = cmds.rename(targ, name + '_' + targetNames[t] + '_targ')
        cmds.parentConstraint(targetList[t], targ, mo=1)
        targets.append(targ)

    # Point constraint
    if point:
        pointEnumString = ''
        for t in targetNames:
            pointEnumString += (t+':')
        p = cmds.pointConstraint(targets, const_grp)
        cmds.addAttr(settingsNode, longName='%s_translate_parent' % name, at='enum', enumName=pointEnumString, keyable=True)
        # Set driven keys to drive the weights of the targets in the point constraint
        pointWeightAliasList = [ str(w) for w in cmds.pointConstraint( const_grp, q=True, weightAliasList=True ) ]

        for spaceIndex in range( len(targetList) ):

            for w in range( len(pointWeightAliasList) ):

                attr = pointWeightAliasList[w]

                if spaceIndex == w:
                    keyValue = 1
                else:
                    keyValue = 0

                cmds.setDrivenKeyframe(
                    p,
                    attribute = attr,
                    currentDriver = (settingsNode + '.%s_translate_parent' % name),
                    driverValue = (spaceIndex),
                    inTangentType = 'linear',
                    outTangentType = 'linear',
                    value = keyValue,
                )

    # Orient constraint
    if orient:
        orientEnumString = ''
        for t in targetNames:
            orientEnumString += (t+':')
        o = cmds.orientConstraint(targets, const_grp)
        cmds.addAttr(settingsNode, longName='%s_rotate_parent' % name, at='enum', enumName=orientEnumString, keyable=True)
        # Set driven keys to drive the weights of the targets in the orient constraint
        orientWeightAliasList = [ str(w) for w in cmds.orientConstraint( const_grp, q=True, weightAliasList=True ) ]
        for spaceIndex in range( len(targetList) ):
            for w in range( len(orientWeightAliasList) ):
                attr = orientWeightAliasList[w]

                if spaceIndex == w:
                    keyValue = 1
                else:
                    keyValue = 0

                cmds.setDrivenKeyframe(
                    o,
                    attribute = attr,
                    currentDriver = (settingsNode + '.%s_rotate_parent' % name),
                    driverValue = (spaceIndex),
                    inTangentType = 'linear',
                    outTangentType = 'linear',
                    value = keyValue,
                )

    if parent:
        parentEnumString = ''
        for t in targetNames:
            parentEnumString += (t+':')
        o = cmds.parentConstraint(targets, const_grp)
        cmds.addAttr(settingsNode, longName='%s_parent_space' % name, at='enum', enumName=parentEnumString, keyable=True)
        # Set driven keys to drive the weights of the targets in the orient constraint
        parentWeightAliasList = [ str(w) for w in cmds.parentConstraint( const_grp, q=True, weightAliasList=True ) ]
        for spaceIndex in range( len(targetList) ):
            for w in range( len(parentWeightAliasList) ):
                attr = parentWeightAliasList[w]

                if spaceIndex == w:
                    keyValue = 1
                else:
                    keyValue = 0

                cmds.setDrivenKeyframe(
                    o,
                    attribute = attr,
                    currentDriver = '%s.%s_parent_space' % (settingsNode, name),
                    driverValue = (spaceIndex),
                    inTangentType = 'linear',
                    outTangentType = 'linear',
                    value = keyValue,
                )