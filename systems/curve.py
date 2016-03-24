import maya.cmds as cmds
from rooftops.core import common

def curveBetweenNodes(start=None, end=None, name=''):
    '''
    Makes a degree 3 nurbs curve with 4 cvs between two nodes
    
    '''
    # Validation of args
    startPos, endPos = None, None
    if not start or not end and len( cmds.ls( sl=True ) ) == 2:
        startPos = cmds.xform( cmds.ls( sl=True )[0], translation=True, query=True, ws=True )
        endPos = cmds.xform( cmds.ls( sl=True )[1], translation=True, query=True, ws=True )
    else:
        if type( start ) == type( 'hello' ) or type( start ) == type( u'hello' ):
            startPos = cmds.xform( str(start), translation=True, query=True, ws=True )
        else:
            startPos = start
            
        if type( end ) == type( 'hello' ) or type( end ) == type( u'hello' ):    
            endPos = cmds.xform( str(end), translation=True, query=True, ws=True )
        else:
            endPos = end

    if not startPos or not endPos:
        return common.showDialog( 'Argument Error', 'Cannot determine start and end points' )
    
    points = common.pointsAlongVector(start=startPos, end=endPos, divisions=3)
    
    # create the curve
    crv = cmds.curve(p=points, k=[0,0,0,1,1,1], name='%s_crv' % name)
    return crv


######################################################################################################################################################


def nodesAlongCurve(crv=None, numNodes=6, name='', followAxis='x', upAxis='y', upNode=None, upVec=None):
    '''
    creates a motionPath node for each in numNodes and connects its parameter to the supplied curve
    attaches an empty group to each motionpath node
    returns a dictionary with keys for the motionPath nodes and the groups along the curve as well as the rootGrp
    upVec can be passed as an attribute eg translation which worldUpVector of motionpath node can be connected to
    '''
    # Validation of args
    if not crv:
        if len(cmds.ls(sl=1)) == 1:
            crv = cmds.ls(sl=1)[0]
        else:
            return common.showDialog( 'Argument Error', 'Please supply or select a nurbs curve' )
        
    upDict = {'x':(1.0, 0.0, 0.0), 'y':(0.0, 1.0, 0.0), 'z':(0.0, 0.0, 1.0)}
    
    #rootGrp = cmds.group(empty=1, name='%s_pathNodes_grp' % name)
    #cmds.setAttr('%s.inheritsTransform' % rootGrp, 0)
    
    returnDict={'mpNodes':[], 'grps':[]}
       
    for i in range( numNodes ):
        n = cmds.group(empty=1, name='%s_%s_grp' % (name, i+1))
        #cmds.parent(n, rootGrp)
        mp = cmds.pathAnimation(n, fm=1, f=1, fa=followAxis, ua=upAxis, wu=upDict[upAxis], curve=crv, name='%s_%s_mp' % (name, i+1))
        if upNode:
            cmds.pathAnimation(mp, e=1, wut='objectrotation', wuo=upNode)
        elif upVec:
            cmds.connectAttr(upVec, '%s.worldUpVector' % mp)
        
        # Delete all the crap that comes with the motion path node
        mpAnim = cmds.listConnections( '%s.uValue' % mp, d=False, s=True, type='animCurve' )
        adlX = cmds.listConnections( '%s.xCoordinate' % mp, d=True, s=False, type='addDoubleLinear' )
        cmds.delete(adlX)
        adlY = cmds.listConnections( '%s.yCoordinate' % mp, d=True, s=False, type='addDoubleLinear' )
        cmds.delete(adlY)
        adlZ = cmds.listConnections( '%s.zCoordinate' % mp, d=True, s=False, type='addDoubleLinear' )
        cmds.delete(adlZ)
        cmds.delete(mpAnim)
        
        # Manually connect up the position
        cmds.connectAttr('%s.xCoordinate' % mp, '%s.tx' % n, f=1)
        cmds.connectAttr('%s.yCoordinate' % mp, '%s.ty' % n, f=1)
        cmds.connectAttr('%s.zCoordinate' % mp, '%s.tz' % n, f=1)
        
        if numNodes != 1:
            cmds.setAttr('%s.uValue' % mp, (1.0 / (numNodes-1))*i)
        else:
            cmds.setAttr('%s.uValue' % mp, 0.5)
        
        returnDict['mpNodes'].append(mp)
        returnDict['grps'].append(n)
        
    return returnDict
        
######################################################################################################################################################

def curveThroughPoints(points=None, name='', bezier=0):
    if not points:
        points = cmds.ls(sl=1, type='transform')

    positions = [cmds.xform(p, q=1, ws=1, t=1) for p in points]

    if len(positions) < 4:
        return 'Please supply at least 4 points'

    numKnots = len(positions) + 2
    knots = []

    for i in range(numKnots):
        if i < 2:
            knots.append(0)
        elif i > numKnots - 3:
            knots.append(numKnots - 5)
        else:
            knots.append(i-2)

    crv = cmds.curve(bezier=bezier, d=3, p=positions, k=knots, name='%s_crv' % name)
    return crv

######################################################################################################################################################

def bindCurve(crv=None):
    '''
    Creates a joint for each cv in the supplied or selected curve
    performs a smooth bind on the curve to the joints
    returns a list of the newly created joints
    
    '''
    # Validation of args
    if not crv:
        if len(cmds.ls(sl=1)) == 1:
            crv = cmds.ls(sl=1)[0]
        else:
            return common.showDialog( 'Argument Error', 'Please supply or select a nurbs curve' )
        
    jointList = []
        
    cvs = cmds.getAttr("%s.cv[*]" % crv)
    
    for cv in range(len(cvs)):
        cmds.select(clear=1)
        j = cmds.joint(p=cvs[cv], name='%s_%s_jnt' %(crv, cv+1))
        jointList.append(j)
        
    cmds.skinCluster(jointList, crv, tsb=1, name='%s_skinCluster' % crv)
    
    return jointList

######################################################################################################################################################

class TangentCurve(object):
    '''
    Creates a bezier curve which automatically adjusts its tangents to maintain clean curvature.
    Creates a control at each point in points with a weight attribute to control tangent lengths
    If closed == true. Creates a closed curve.
    '''
    def __init__(self, points=None, name='', closed=False):
        super(TangentCurve, self).__init__()
        if points:
            self.points = points
        else:
            self.points = cmds.ls(sl=1)
        if not self.points:
            return 'please supply or select at least 3 points to create a tangentCurve'
        self.name = name
        self.closed = closed
        self.build()

    def buildSpan(self, points, index):
        main_grp = cmds.group(empty=1, name='%s_span_%s_grp' % (self.name, str(index)))
        shapes = [cmds.listRelatives(p, c=1, s=1)[0] for p in points]
        midA = cmds.spaceLocator(name='%s_span_%s_mid_A_loc' % (self.name, str(index)))[0]
        cmds.pointConstraint(points[0], points[1], midA)
        cmds.parent(midA, main_grp)
        midB = cmds.spaceLocator(name='%s_span_%s_mid_B_loc' % (self.name, str(index)))[0]
        cmds.pointConstraint(points[1], points[2], midB)
        cmds.parent(midB, main_grp)

        # Create curve and connect curve points
        crv = curveBetweenNodes(points[0], points[2], '%s_span_%s' % (self.name, str(index)))
        cmds.parent(crv, main_grp)
        crvShape = cmds.listRelatives(crv, c=1, s=1)[0]
        cmds.connectAttr('%s.worldPosition[0]' % shapes[0], '%s.controlPoints[%s]' % (crvShape, 0))
        cmds.connectAttr('%s.worldPosition[0]' % cmds.listRelatives(midA, c=1, s=1)[0], '%s.controlPoints[%s]' % (crvShape, 1))
        cmds.connectAttr('%s.worldPosition[0]' % cmds.listRelatives(midB, c=1, s=1)[0], '%s.controlPoints[%s]' % (crvShape, 2))
        cmds.connectAttr('%s.worldPosition[0]' % shapes[2], '%s.controlPoints[%s]' % (crvShape, 3))

        # Motionpath node
        mp = nodesAlongCurve(crv, numNodes=1, name='%s_span_%s' % (self.name, str(index)), upNode=points[1])
        npc = cmds.createNode('nearestPointOnCurve', name='%s_span_%s' % (self.name, str(index)))
        cmds.connectAttr('%s.worldPosition[0]' % shapes[1], '%s.inPosition' % npc)
        cmds.connectAttr('%s.worldSpace[0]' % crvShape, '%s.inputCurve' % npc)
        cmds.connectAttr('%s.parameter' % npc, '%s.uValue' % mp['mpNodes'][0])
        cmds.setAttr('%s.fractionMode' % mp['mpNodes'][0], 0)
        cmds.parent(mp['grps'][0], main_grp)

        # Tangents
        tanGrp = cmds.group(empty=1, name='%s_span_%s_tangent_grp' % (self.name, str(index)))
        common.align(tanGrp, points[1])
        cmds.parent(tanGrp, points[1])
        cmds.orientConstraint(mp['grps'][0], tanGrp)

        inTan_loc = cmds.spaceLocator(name='%s_span_%s_inTangent_loc' % (self.name, str(index)))[0]
        common.align(inTan_loc, tanGrp)
        cmds.parent(inTan_loc, tanGrp)
        inDist = cmds.createNode('distanceBetween', name='%s_span_%s_in_dist' % (self.name, str(index)))
        cmds.connectAttr('%s.worldPosition[0]' % shapes[0], '%s.point1' % inDist)
        cmds.connectAttr('%s.worldPosition[0]' % shapes[1], '%s.point2' % inDist)

        outTan_loc = cmds.spaceLocator(name='%s_span_%s_outTangent_loc' % (self.name, str(index)))[0]
        common.align(outTan_loc, tanGrp)
        cmds.parent(outTan_loc, tanGrp)
        outDist = cmds.createNode('distanceBetween', name='%s_span_%s_out_dist' % (self.name, str(index)))
        cmds.connectAttr('%s.worldPosition[0]' % shapes[1], '%s.point1' % outDist)
        cmds.connectAttr('%s.worldPosition[0]' % shapes[2], '%s.point2' % outDist)

        weight_md = cmds.createNode('multiplyDivide', name='%s_span_%s_weight_md' % (self.name, str(index)))
        cmds.connectAttr('%s.distance' % inDist, '%s.input1X' % weight_md)
        cmds.connectAttr('%s.distance' % outDist, '%s.input1Y' % weight_md)
        cmds.setAttr('%s.input2X' % weight_md, 0.25)
        cmds.setAttr('%s.input2Y' % weight_md, 0.25)

        weight_uc = cmds.createNode('unitConversion', name='%s_span_%s_weight_invert_uc' % (self.name, str(index)))
        cmds.setAttr('%s.conversionFactor' % weight_uc, -1.0)
        cmds.connectAttr('%s.outputX' % weight_md, '%s.input' % weight_uc)

        cmds.connectAttr('%s.outputY' % weight_md, '%s.tx' % outTan_loc)
        cmds.connectAttr('%s.output' % weight_uc, '%s.tx' % inTan_loc)

        # weight attribute to control tangent lengths
        self.addWeightAttr(node=points[1], md=weight_md)

        return{
            'inTan':inTan_loc,
            'outTan':outTan_loc,
            'inDist':inDist,
            'outDist':outDist,
            'weight_md':weight_md,
            'main_grp':main_grp,
        }

    def addWeightAttr(self, node, md):
        cmds.addAttr(node, ln='tangentWeight', at="float", minValue=0.0, maxValue=1.0, keyable=1, hidden=0, defaultValue=0.25 )
        cmds.connectAttr('%s.tangentWeight' % node, '%s.input2X' % md)
        cmds.connectAttr('%s.tangentWeight' % node, '%s.input2Y' % md)


    def build(self):
        self.dnt_grp = cmds.group(empty=1, name='%s_doNotTouch' % self.name)
        cmds.setAttr('%s.inheritsTransform' % self.dnt_grp, 0)
        numSpans = len(self.points)-2
        self.cv_locs = []
        self.spans = []
        for i in range(len(self.points)):
            loc = cmds.spaceLocator(name = '%s_cv_%s_loc' % (self.name, str(i)))[0]
            common.align(loc, self.points[i])
            self.cv_locs.append(loc)
        for i in range(numSpans):
            span = self.buildSpan(self.cv_locs[i:i+3], i)
            cmds.parent(span['main_grp'], self.dnt_grp)
            self.spans.append(span)

        if not self.closed:
            # Build start tangent
            tanGrp = cmds.group(empty=1, name='%s_start_tangent_grp' % self.name)
            common.align(tanGrp, self.cv_locs[0])
            cmds.parent(tanGrp, self.cv_locs[0])
            cmds.aimConstraint(self.spans[0]['inTan'], tanGrp, wut='objectrotation', wuo=self.cv_locs[0])

            outTan_loc = cmds.spaceLocator(name='%s_start_outTangent_loc' % self.name)[0]
            common.align(outTan_loc, tanGrp)
            cmds.parent(outTan_loc, tanGrp)

            weight_md = cmds.createNode('multiplyDivide', name='%s_start_weight_md' % self.name)
            cmds.connectAttr('%s.distance' % self.spans[0]['inDist'], '%s.input1X' % weight_md)
            cmds.setAttr('%s.input2X' % weight_md, 0.33)

            cmds.connectAttr('%s.outputX' % weight_md, '%s.tx' % outTan_loc)

            self.addWeightAttr(self.cv_locs[0], weight_md)

            # Build end tangent
            tanGrp = cmds.group(empty=1, name='%s_end_tangent_grp' % self.name)
            common.align(tanGrp, self.cv_locs[-1])
            cmds.parent(tanGrp, self.cv_locs[-1])
            cmds.aimConstraint(self.spans[-1]['outTan'], tanGrp, wut='objectrotation', wuo=self.cv_locs[-1])

            inTan_loc = cmds.spaceLocator(name='%s_end_inTangent_loc' % self.name)[0]
            common.align(inTan_loc, tanGrp)
            cmds.parent(inTan_loc, tanGrp)

            weight_md = cmds.createNode('multiplyDivide', name='%s_endt_weight_md' % self.name)
            cmds.connectAttr('%s.distance' % self.spans[-1]['outDist'], '%s.input1X' % weight_md)
            cmds.setAttr('%s.input2X' % weight_md, 0.33)

            cmds.connectAttr('%s.outputX' % weight_md, '%s.tx' % inTan_loc)

            self.addWeightAttr(self.cv_locs[-1], weight_md)

            self.spans.append({
                'endTan':inTan_loc,
                'startTan':outTan_loc,
            })

            # Collect points for curve
            self.crv_points = [self.cv_locs[0], self.spans[-1]['startTan']]
            for i in range(len(self.spans)-1):
                self.crv_points.append(self.spans[i]['inTan'])
                #self.crv_points.append(self.cv_locs[i+1])
                self.crv_points.append(self.spans[i]['outTan'])
            self.crv_points.append(self.spans[-1]['endTan'])
            self.crv_points.append(self.cv_locs[-1])

            # Create curve and connect points
            self.crv = curveThroughPoints(points=self.crv_points, name=self.name)
            cmds.parent(self.crv, self.dnt_grp)


            for i in range(len(self.crv_points)):
                crvShape = cmds.listRelatives(self.crv, c=1, s=1)[0]
                cmds.connectAttr('%s.worldPosition[0]' % self.crv_points[i], '%s.controlPoints[%s]' % (crvShape, i))

        else:
            self.spans.append(self.buildSpan([self.cv_locs[-2], self.cv_locs[-1], self.cv_locs[0]], numSpans + 1))
            self.spans.append(self.buildSpan([self.cv_locs[-2], self.cv_locs[-1], self.cv_locs[0]], numSpans + 2))

######################################################################################################################################################
import pymel.core as pmc
#import rooftops.systems.curve as rtCurve

def getPyNode(node):
    '''
    returns a pynode  wrapping the given node
    '''
    pynode=pmc.ls(node)[0]
    return pynode

def blendVectors(vec1, vec2, name, driver=None):
    '''
    creates a blendColors node with vec1 and vec2 as inputs
    if supplied, connects the blender attribute to the driver attribute
    '''
    bc = pmc.createNode('blendColors', name='%s_bc' % name)
    pmc.connectAttr(vec1, bc.color1)
    pmc.connectAttr(vec2, bc.color2)
    if driver:
        pmc.connectAttr(driver, bc.blender)
    return bc

class CompressSegment(object):
    '''
    startVec, endVec and normalVec should be passed in as attributes to which things can be connected

    '''
    def __init__(self, startVec, endVec, normalVec, crv=None, name='', samples=6, twistAttr=None):
        super(CompressSegment, self).__init__()
        self.name=name
        self.crv=None
        if crv:
            self.crv = getPyNode(crv)
            self.crvShape = pmc.listRelatives(self.crv, c=1, s=1)[0]

        self.build(startVec, endVec, normalVec, samples, twistAttr)

    def build(self, startVec, endVec, normalVec, samples, twistAttr):
        if self.crv:
            for i in range(samples):
                param = 1.0 / (samples+1) * (i+1)

                loc = pmc.spaceLocator(name='%s_%s_loc' % (self.name, i+1))
                #loc.rotateOrder.set(1)

                mp = pmc.createNode('motionPath', name='%s_%s_mp' % (self.name, i+1))
                mp.follow.set(1)
                mp.fractionMode.set(1)
                mp.frontAxis.set(0)
                mp.upAxis.set(1)
                mp.uValue.set(param)
                pmc.connectAttr(normalVec, mp.worldUpVector)
                self.crvShape.worldSpace[0].connect(mp.geometryPath)

                grp = pmc.group(empty=1, name='%s_%s_grp' % (self.name, i+1))
                loc.setParent(grp)
                mp.allCoordinates.connect(grp.t)
                mp.rotate.connect(grp.r)
                grp.inheritsTransform.set(1)

                startEndBc = blendVectors(endVec, startVec, '%s_%s_startEnd' % (self.name, i+1))
                mp.uValue.connect(startEndBc.blender)

                # Construct matrix
                bridgeVp = pmc.createNode('vectorProduct', name='%s_%s_bridge_vp' % (self.name, i+1))
                bridgeVp.operation.set(2)
                pmc.connectAttr(normalVec, bridgeVp.input1)
                startEndBc.output.connect(bridgeVp.input2)
                bridgeVp.normalizeOutput.set(1)

                yVp = pmc.createNode('vectorProduct', name='%s_%s_y_vp' % (self.name, i+1))
                yVp.operation.set(2)
                startEndBc.output.connect(yVp.input1)
                bridgeVp.output.connect(yVp.input2)
                yVp.normalizeOutput.set(1)

                zVp = pmc.createNode('vectorProduct', name='%s_%s_z_vp' % (self.name, i+1))
                zVp.operation.set(2)
                startEndBc.output.connect(zVp.input1)
                yVp.output.connect(zVp.input2)
                zVp.normalizeOutput.set(1)

                mat = pmc.createNode('fourByFourMatrix', name='%s_%s_matrix' % (self.name, i+1))
                startEndBc.outputR.connect(mat.in00)
                startEndBc.outputG.connect(mat.in01)
                startEndBc.outputB.connect(mat.in02)

                yVp.outputX.connect(mat.in10)
                yVp.outputY.connect(mat.in11)
                yVp.outputZ.connect(mat.in12)

                zVp.outputX.connect(mat.in20)
                zVp.outputY.connect(mat.in21)
                zVp.outputZ.connect(mat.in22)

                multMat = pmc.createNode('multMatrix',  name='%s_%s_multMatrix' % (self.name, i+1))
                mat.output.connect(multMat.matrixIn[0])
                grp.worldInverseMatrix[0].connect(multMat.matrixIn[1])

                twistUC = pmc.createNode('unitConversion', name='%s_%s_twist_uc' % (self.name, i+1))
                twistUC.conversionFactor.set(param)

                pmc.select(loc)
                j = pmc.joint(name='%s_%s_jnt' % (self.name, i+1))

                dMat = pmc.createNode('decomposeMatrix', name='%s_%s_decomposeMatrix' % (self.name, i+1))
                multMat.matrixSum.connect(dMat.inputMatrix)
                #dMat.inputRotateOrder.set(1)
                dMat.outputRotate.connect(loc.r)
                twistUC.output.connect(j.rx)
                if twistAttr:
                    pmc.connectAttr(twistAttr, twistUC.input)

                # Set up scaling
                pmc.addAttr(grp, ln='volume_hold', at='float', keyable=1, hidden=0, minValue=0.0, maxValue=1.0)

                # Y
                yScaleBlend = pmc.createNode('blendTwoAttr', name='%s_%s_yScale_blend' % (self.name, i+1))
                grp.volume_hold.connect(yScaleBlend.attributesBlender)
                yScaleBlend.output.connect(loc.sy)

                yScaleMd = pmc.createNode('multiplyDivide', name='%s_%s_yScale_md' % (self.name, i+1))
                yScaleMd.operation.set(2)
                yScaleMd.input1X.set(1.0)
                yScaleMd.input1Y.set(1.0)
                yScaleMd.input1Z.set(1.0)
                yScaleMd.outputX.connect(yScaleBlend.input[0])
                yScaleMd.outputY.connect(yScaleBlend.input[1])

                yScaleVp = pmc.createNode('vectorProduct', name='%s_%s_yScale_vp' % (self.name, i+1))
                yScaleVp.operation.set(3)
                multMat.matrixSum.connect(yScaleVp.matrix)
                yScaleVp.input1X.set(0.0)
                yScaleVp.input1Y.set(1.0)
                yScaleVp.input1Z.set(0.0)
                yScaleVp.outputY.connect(yScaleMd.input2Y)

                # Z
                zScaleBlend = pmc.createNode('blendTwoAttr', name='%s_%s_zScale_blend' % (self.name, i+1))
                grp.volume_hold.connect(zScaleBlend.attributesBlender)
                zScaleBlend.output.connect(loc.sz)

                zScaleMd = pmc.createNode('multiplyDivide', name='%s_%s_zScale_md' % (self.name, i+1))
                zScaleMd.operation.set(2)
                zScaleMd.input1X.set(1.0)
                zScaleMd.input1Y.set(1.0)
                zScaleMd.input1Z.set(1.0)
                zScaleMd.outputX.connect(zScaleBlend.input[0])
                zScaleMd.outputZ.connect(zScaleBlend.input[1])

                zScaleVp = pmc.createNode('vectorProduct', name='%s_%s_zScale_vp' % (self.name, i+1))
                zScaleVp.operation.set(3)
                multMat.matrixSum.connect(zScaleVp.matrix)
                zScaleVp.input1X.set(0.0)
                zScaleVp.input1Y.set(0.0)
                zScaleVp.input1Z.set(1.0)
                zScaleVp.outputZ.connect(zScaleMd.input2Z)


#testSeg = CompressSegment('upArm_tangent_vp.output', 'lowArm_tangent_vp.output', 'upArm_normal_vp.output', crv='upArm_crv', twistAttr='lowArm_nonRoll_info.rx')









