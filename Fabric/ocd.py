import pymel.core as pmc
import maya.OpenMaya as om

class Ocd_Segment(object):
    def __init__(self, ctrls=None, samples=12, name=''):
        super(Ocd_Segment, self).__init__()
        self.ctrls = ctrls
        self.samples = samples
        self.name=name
        self.vec3s = []
        self.pushes = []
        self.ports=[]
        self.build()
    
    def build(self):    
        # Create canvas node
        self.cn = pmc.createNode('canvasNode', name=self.name)

        # create a vec3 for the position of each in ctrls (using decompose matrix nodes for now)
        for c in range(len(self.ctrls)):
            v = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Exts.Math.Constants.Vec3', x=c*300, y=c*100)
            self.vec3s.append(v)

            p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=c*300+150, y=c*100)
            self.pushes.append(p)

            # create ports
            port = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='ctrl_%s' % str(c+1), p='In', t='Vec3')
            self.ports.append(port)

            # get world space of control by creating a decompose matrix node and connecting it to the control's world matrix
            con = pmc.listConnections(self.ctrls[c], type='decomposeMatrix')
            dMat = None
            if not con:
                dMat = pmc.createNode('decomposeMatrix', n='%s_worldSpace_decomposeMatrix' % self.ctrls[c])
                pmc.connectAttr('%s.worldMatrix[0]' % self.ctrls[c], '%s.inputMatrix' % dMat)
            else:
                dMat = con[0]


            # Make connections
            pmc.connectAttr('%s.outputTranslate' % dMat, '%s.ctrl_%s' %(self.cn.getName(), c+1))

            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s=port, d='%s.value' % v)

            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.value' % v, d='%s.element' % p)

            if c > 0:
                pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.pushes[c-1], d='%s.array' % p)

        # create segment preset + associated ports / connections
        self.sampler = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='User.curveSampler', x=(len(self.ctrls)+1)*300+100, y=100)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.pushes[-1], d='%s.ctrls' % self.sampler)

        self.samplesPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='samples', p='In', t='UInt32')
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s=self.samplesPort, d='%s.samples' % self.sampler)
        pmc.setAttr('%s.samples' % self.cn.getName(), self.samples)

        self.resultPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='result', p='Out', t='Vec3[]')
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.result' % self.sampler, d=self.resultPort)


class Ocd_Chain(object):
    def __init__(self, name=''):
        super(Ocd_Chain, self).__init__()
        self.name=name
        self.segments=[]
        self.pushes=[]

        self.build()

    def addSegment(self, segment):
        '''
        expects an instance of Ocd_Segment passed as 'segmemnt'
        '''
        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.pushes)*300+100, y=len(self.pushes)*100+100)

        # Create input port and connections
        port = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d=segment.name, p='In', t='Vec3[]', c='%s.element' % p)
        pmc.connectAttr('%s.result[0]' % segment.name, '%s.%s[0]' % (self.cn.getName(), port))
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % p, d='%s.positions' % self.chain)
        if self.pushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.pushes[-1], d='%s.array' % p)

        self.pushes.append(p)

    def build(self):
        # Create canvas node
        self.cn = pmc.createNode('canvasNode', name=self.name)

        # create chain preset and output ports
        self.chain = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='User.chain', x=500, y=100)
        self.bendsPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='bends', p='Out', t='Float32[]', c='%s.bends' % self.chain)
        self.cmpVecsPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='cmpVecs', p='Out', t='Vec3[]', c='%s.cmpVecs' % self.chain)
        self.xfosPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='xfos', p='Out', ui='{"uiHidden" : "","uiOpaque" : "true","uiPersistValue" : "","uiRange" : "","uiHardRange" : "","uiCombo" : ""}', t='Vec3[]')
        pmc.FabricCanvasEditPort(m=self.cn.getName(), e="", n="xfos", d="xfos", t="Xfo[]")


#seg = Ocd_Segment(ctrls=pmc.selected(type='transform'), name='seg_1')
#chain = Ocd_Chain(name='chain_1')
#chain.addSegment(seg)
