import maya.cmds as cmds
from ROOFTOPS.core import common

def build( joint=None, name='' ):
    '''
    Creates a duplicate of the specified joint which will remove the twist.
    Based on Victor Vinyals' nonroll setup
    Duplicates the joint and deletes all children apart from the first child joint ( there must at least a single child joint in the hierarchy )
    Creates an RP IKHandle with the pole vector set to zero
    Parents the pole vector to the original joint
    
    point constrains the nonRoll to the joint
    
    groups the nonRoll outside the hierarchy
    
    Also creates an 'info' locator which is parented to 'nonRoll' and aim constrained to 'nonRollEnd' using 'joint' as its up vector -
         - this is the node from which to read the twist value
    
    '''

        
    if not joint and len( cmds.ls( sl=1, type='joint' ) ) == 1:
        joint = cmds.ls( sl=1, type='joint' )[ 0 ]
        
    if joint and cmds.listRelatives( joint, c=1, type='joint' ):
        end = cmds.listRelatives( joint, c=1, type='joint' )[ 0 ]
    else:
        raise RuntimeError, 'You must specify a joint which has a child joint in its hierarchy'

    # main group for nonRoll system
    main_grp = cmds.group( empty=1, name='%s_nonRoll_grp' % name )
    common.align( main_grp, joint )
    
    # Duplicate the joints and delete all but first child joint
    copies = cmds.duplicate( joint, name='%s_nonRoll' % name, rc=1 )
    nonRoll = copies[ 0 ]
    nonRollEnd = cmds.listRelatives( nonRoll, c=1, type='joint' )[ 0 ]
    deleteList = [ c for c in copies if not c in [ nonRoll, nonRollEnd ] ]
    if deleteList:
        cmds.delete( deleteList )        
    nonRollEnd = cmds.rename( nonRollEnd, '%s_nonRoll_end' % name )
    
    rad = cmds.getAttr( '%s.radius' % nonRoll ) * 1.5
    cmds.setAttr( '%s.radius' % nonRoll, rad )
    cmds.setAttr( '%s.radius' % nonRollEnd, rad )
    
    cmds.parent( nonRoll, main_grp )
    cmds.pointConstraint( joint, nonRoll )
    
    # build ikHandle
    ikHandle = cmds.ikHandle( sj=nonRoll, ee=nonRollEnd, n='%s_nonRoll_ikHandle' % name, sol='ikRPsolver' )[ 0 ]
    cmds.setAttr( '%s.poleVectorX' % ikHandle, 0 )
    cmds.setAttr( '%s.poleVectorY' % ikHandle, 0 )
    cmds.setAttr( '%s.poleVectorZ' % ikHandle, 0 )
    
    cmds.parent( ikHandle, joint )
    
    # build info locator
    info = cmds.spaceLocator( n='%s_nonRoll_info' % name )[ 0 ]
    common.align( info, joint )
    cmds.parent( info, nonRoll )
    
    if cmds.getAttr( '%s.tx' % end ) < 0:
        aimVec = ( -1, 0, 0 )
    else:
        aimVec = ( 1, 0, 0 )
    cmds.aimConstraint( nonRollEnd, info, aimVector=aimVec, wut='objectrotation', wuo=joint )
    
    returnDict = {'main_grp':main_grp, 'nonRoll':nonRoll, 'info':info, 'ikHandle':ikHandle}
    return returnDict


