import pymel.core as pmc
import maya.OpenMaya as om

def createSegment(ctrls=None, samples=12, name=''):
    # Create canvas node
    cn = pmc.createNode('canvasNode', name='%s_segment' % name)

    # create a vec3 for the position of each in ctrls (using decompose matrix nodes for now)
    vec3s = []
    pushes = []
    ports=[]
    for c in range(len(ctrls)):
        v = pmc.FabricCanvasInstPreset(m=cn.getName(), e='', p='Fabric.Exts.Math.Constants.Vec3', x=c*300, y=c*100)
        vec3s.append(v)

        p = pmc.FabricCanvasInstPreset(m=cn.getName(), e='', p='Fabric.Core.Array.Push', x=c*300+150, y=c*100)
        pushes.append(p)

        # create ports
        port = pmc.FabricCanvasAddPort(m=cn.getName(), e='', d='ctrl_%s' % str(c+1), p='In', t='Vec3')
        ports.append(port)

        # get world space of control by creating a decompose matrix node and connecting it to the control's world matrix
        con = pmc.listConnections(ctrls[c], type='decomposeMatrix')
        dMat = None
        if not con:
            dMat = pmc.createNode('decomposeMatrix', n='%s_worldSpace_decomposeMatrix' % ctrls[c])
            pmc.connectAttr('%s.worldMatrix[0]' % ctrls[c], '%s.inputMatrix' % dMat)
        else:
            dMat = con[0]


        # Make connections
        pmc.connectAttr('%s.outputTranslate' % dMat, '%s.ctrl_%s' %(cn.getName(), c+1))

        pmc.FabricCanvasConnect(m=cn.getName(), e='', s=port, d='%s.value' % v)

        pmc.FabricCanvasConnect(m=cn.getName(), e='', s='%s.value' % v, d='%s.element' % p)

        if c > 0:
            pmc.FabricCanvasConnect(m=cn.getName(), e='', s='%s.array' % pushes[c-1], d='%s.array' % p)

    # create segment preset + associated ports / connections
    s = pmc.FabricCanvasInstPreset(m=cn.getName(), e='', p='User.curveSampler', x=(len(ctrls)+1)*300, y=100)
    pmc.FabricCanvasConnect(m=cn.getName(), e='', s='%s.array' % pushes[-1], d='%s.ctrls' % s)

    samplesPort = pmc.FabricCanvasAddPort(m=cn.getName(), e='', d='samples', p='In', t='UInt32')
    pmc.FabricCanvasConnect(m=cn.getName(), e='', s=samplesPort, d='%s.samples' % s)

    resultPort = pmc.FabricCanvasAddPort(m=cn.getName(), e='', d='result', p='Out', t='Vec3[]')
    pmc.FabricCanvasConnect(m=cn.getName(), e='', s='%s.result' % s, d=resultPort)


    return {'canvasNode':cn, 'vec3s':vec3s, 'pushes':pushes}

seg = createSegment(ctrls=pmc.selected(type='transform'), name='chain_1_a')
