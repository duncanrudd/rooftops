import pymel.core as pmc
import maya.mel as mel
import maya.OpenMaya as om

def createSegment(ctrls=None, samples=12, name=''):
    # Create canvas node
    cn = pmc.createNode('canvasNode', name='%s_segment' % name)

    # create a vec3 for the position of each in ctrls (using decompose matrix nodes for now)
    vec3s = []
    pushes = []
    ports=[]
    for c in range(len(ctrls)):
        cmd = 'FabricCanvasInstPreset -m "%s" -e "" -p "Fabric.Exts.Math.Constants.Vec3" -x "%s" -y "%s";' % (cn.getName(), c*300, c*100)
        v = mel.eval(cmd)
        vec3s.append(v)

        cmd = 'FabricCanvasInstPreset -m "%s" -e "" -p "Fabric.Core.Array.Push" -x "%s" -y "%s";' % (cn.getName(), c*300+150, c*100)
        p = mel.eval(cmd)
        pushes.append(p)

        # create ports
        cmd = 'FabricCanvasAddPort -m "%s" -e "" -d "ctrl_%s" -p "In" -t "Vec3";' % (cn.getName(), c+1)
        port = mel.eval(cmd)
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

        cmd = 'FabricCanvasConnect -m "%s" -e "" -s "%s" -d "%s.value";' % (cn.getName(), port, v)
        mel.eval(cmd)

        cmd = 'FabricCanvasConnect -m "%s" -e "" -s "%s.value" -d "%s.element";' % (cn.getName(), v, p)
        mel.eval(cmd)

        if c > 0:
            cmd = 'FabricCanvasConnect -m "%s" -e "" -s "%s.array" -d "%s.array";' % (cn.getName(), pushes[c-1], p)
            mel.eval(cmd)

    # create segment preset
    #cmd = 'FabricCanvasInstPreset -m "%s" -e "" -p "Fabric.Presets.User.segment" -x "%s";' % (cn.getName(), (len(ctrls)+1)*300)
    #s = mel.eval(cmd)

    #cmd = 'FabricCanvasConnect -m "%s" -e "" -s "%s.array" -d "%s.ctrls";' % (cn.getName(), pushes[-1], s)
    #mel.eval(cmd)

    return {'canvasNode':cn, 'vec3s':vec3s, 'pushes':pushes, 'ports':ports}


#seg = createSegment(ctrls=pmc.selected(type='transform'), name='chain_1_a')
