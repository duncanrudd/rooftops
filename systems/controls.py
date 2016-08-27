import maya.cmds as cmds
from rooftops.core import common
import pymel.core as pmc


def orientCtrl(ctrl=None, axis=None):
    '''
    rotates the cvs of a ctrl to point along axis
    
    '''
    # orient ik_anim cvs properly
    shape = common.getShape(ctrl)
    cmds.select( '%s.cv[ * ]' % shape )
    
    if axis=='y':
        cmds.rotate( 90, rotateX=True )
    elif axis=='x':
        cmds.rotate( 90, rotateY=True )
    else:
        cmds.rotate( 90, rotateZ=True )
        
    cmds.select(clear=1)
    
    
######################################################################################################################################################

def circleCtrl(radius=20.0, name='', axis='z'):
    '''
    creates a circular nurbs curve
    
    '''
    ctrl = pmc.circle(name=name, r=radius, ch=0, o=1)
    
    if axis != 'z':
        orientCtrl(ctrl=ctrl, axis=axis)
    return ctrl

######################################################################################################################################################

def circleBumpCtrl(radius=20.0, name='', axis='z'):
    '''
    creates a circular nurbs curve with a bump to indicate orientation
    
    '''
    ctrl = pmc.circle(name=name, r=radius, ch=0, o=1, s=24)[0]
    
    shape = common.getShape(ctrl.nodeName())
    shape = shape.rename(ctrl.nodeName()+'Shape')
    pmc.select( '%s.cv[ 1 ]' % shape )
    pmc.move(radius*.5, moveY=1, r=1)
    
    if axis != 'z':
        orientCtrl(ctrl=ctrl, axis=axis)
    return ctrl

######################################################################################################################################################

def boxCtrl(size=20.0, name=''):
    '''
    Creates a box shaped nurbs curve
    
    '''
    pos = size * 0.5
    neg = pos*-1
    points = [(neg, pos, neg), (neg, neg, neg), (neg, neg, pos), (neg, pos, pos),
              (neg, pos, neg), (pos, pos, neg), (pos, neg, neg), (neg, neg, neg),
              (neg, neg, pos), (pos, neg, pos), (pos, neg, neg), (pos, pos, neg),
              (pos, pos, pos), (neg, pos, pos), (pos, pos, pos), (pos, neg, pos)]
    
    knots = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
    
    ctrl = pmc.curve(degree=1, p=points, k=knots, name=name)
    
    return ctrl
    
######################################################################################################################################################

def crossCtrl(size=20.0, name='', axis='z'):
    '''
    Creates a locator shaped nurbs curve
    
    '''
    pos = size * 0.5
    neg = pos*-1
    points = [(0, 0, neg), (0, 0, pos), (0, 0, 0), (0, pos, 0),
              (0, neg, 0), (0, 0, 0), (pos, 0, 0), (neg, 0, 0)]
    
    knots = [1,2,3,4,5,6,7,8]
    
    ctrl = pmc.curve(degree=1, p=points, k=knots, name=name)
    
    return ctrl

######################################################################################################################################################

def squareCtrl(size=20.0, name='', axis='y'):
    '''
    creates a square nurbs curve
    
    '''
    pos = size * 0.5
    neg = pos*-1
    points = [(neg, neg, 0), (neg, pos, 0), (pos, pos, 0), (pos, neg, 0), (neg, neg, 0)]
    
    knots = [1,2,3,4,5]
    
    ctrl = pmc.curve(degree=1, p=points, k=knots, name=name)
    if axis != 'z':
        orientCtrl(ctrl=ctrl, axis=axis)
    return ctrl

######################################################################################################################################################

def pinCtrl(radius=20.0, name='', axis='z'):
    '''
    creates a pin control
    
    '''
    axisDict={'x':(radius,0,0), 'y':(0,radius,0), 'z':(0,0,radius)}
    line = pmc.curve(d = 1, p = [(0,0,0), axisDict[axis]], k = [0,1], name=name)
    
    circle = pmc.circle(name=(name + '_circle'), r=radius*.2, ch=0, o=1, s=24)
    if axis != 'z':
        orientCtrl(ctrl=circle, axis=axis)
    shape = pmc.listRelatives(circle, shapes = True)[0]

    cmds.move(axisDict[axis][0], axisDict[axis][1], axisDict[axis][2], "%s.cv[:]" % shape, r = 1)
    
    pmc.parent(shape, line, shape = 1, r = 1)
    shapes = pmc.listRelatives(line, shapes = True)
    shapes[1].rename(shapes[0].nodeName().replace('Shape', 'CircleShape'))
    pmc.delete(circle)
    
    return line









