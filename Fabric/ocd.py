import pymel.core as pmc
import maya.OpenMaya as om

opaqueDict = '{"uiHidden" : "","uiOpaque" : "true","uiPersistValue" : "","uiRange" : "","uiHardRange" : "","uiCombo" : ""}'

def MVectorFromList(list):
    '''
    takes a list of 3 floats and returns an MVector using those values
    '''
    return om.MVector(list[0], list[1], list[2])

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

        self.resultPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='result', p='Out', ui=opaqueDict, t='Vec3[]')
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.result' % self.sampler, d=self.resultPort)


class Ocd_Chain(object):
    def __init__(self, name=''):
        super(Ocd_Chain, self).__init__()
        self.name=name
        self.segments=[]
        self.pushes=[]
        self.bends=[]
        self.bendPushes=[]
        self.cmpVecs=[]
        self.cmpVecPushes=[]

        self.build()

    def addJoint(self, segment):
        '''
        Adds a Float32 node which is pushed into an array and describes the initial bend state of a joint.
        Adds a Vec3 node which is pushed into an array and describes the initial compression vector.
        '''
        b = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Constants.Float32', x=len(self.bends)*300+100, y=len(self.bends)*100+300)
        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.bends)*300+250, y=len(self.bends)*100+350)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.value' % b, d='%s.element' % p)
        if self.bendPushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.bendPushes[-1], d='%s.array' % p)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % p, d='%s.initBends' % self.chain)

        self.bends.append(b)
        self.bendPushes.append(p)

        c = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Exts.Math.Constants.Vec3', x=len(self.bends)*300+100, y=len(self.bends)*100+600)
        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.bends)*300+250, y=len(self.bends)*100+650)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.value' % c, d='%s.element' % p)
        if self.cmpVecPushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.cmpVecPushes[-1], d='%s.array' % p)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % p, d='%s.initCmpVecs' % self.chain)

        self.cmpVecs.append(c)
        self.cmpVecPushes.append(p)



    def initJoints(self):
        bends = pmc.getAttr('%s.bends' % self.cn.getName())
        cmpVecs = [pmc.getAttr('%s.cmpVecs[%s]' % (self.cn.getName(), i)) for i in range(len(bends))]
        for j in range(len(self.bends)):
            pmc.FabricCanvasSetPortDefaultValue(m=self.cn.getName(), e='', p='%s.value' % self.bends[j], t='Scalar', v=bends[j])
            vecDict = '{"x":%s, "y":%s, "z":%s}' % (cmpVecs[j][0], cmpVecs[j][1], cmpVecs[j][2])
            pmc.FabricCanvasSetPortDefaultValue(m=self.cn.getName(), e='', p='%s.value' % self.cmpVecs[j], t='Vec3', v=vecDict)

        pmc.FabricCanvasSetPortDefaultValue(m=self.cn.getName(), e='', p='%s.value' % self.initBool, t='Boolean', v='true')

    def addSegment(self, segment):
        '''
        expects an instance of Ocd_Segment passed as 'segmemnt'
        '''
        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.pushes)*300+100, y=len(self.pushes)*100+100)

        # Create input port and connections
        port = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d=segment.name, p='In', ui=opaqueDict, t='Vec3[]')
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s=port, d='%s.element' % p)
        pmc.connectAttr('%s.result' % segment.name, '%s.%s' % (self.cn.getName(), port))
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % p, d='%s.positions' % self.chain)
        if self.pushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.pushes[-1], d='%s.array' % p)

        self.pushes.append(p)
        self.segments.append(segment)

    def build(self):
        # Create canvas node
        self.cn = pmc.createNode('canvasNode', name=self.name)

        # create chain preset and output ports
        self.chain = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='User.chain', x=500, y=100)
        self.bendsPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='bends', p='Out', t='Float32[]', c='%s.bends' % self.chain)
        self.cmpVecsPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='cmpVecs', p='Out', t='Vec3[]', c='%s.cmpVecs' % self.chain)
        self.xfosPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='xfos', p='Out', ui=opaqueDict, t='Vec3[]')
        pmc.FabricCanvasEditPort(m=self.cn.getName(), e="", n="xfos", d="xfos", t="Xfo[][]")
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.xfos' % self.chain, d=self.xfosPort)
        self.basePort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='base_matrix', p='In', t='Mat44', c='%s.baseMat' % self.chain)

        # Create boolean node - When initial joint values are available,
        # set this to true so bends/compression can be evaluated based on an initial state
        self.initBool = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Constants.Boolean', x=300, y=100)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.value' % self.initBool, d='%s.init' % self.chain)

seg = Ocd_Segment(ctrls=pmc.selected(type='transform'), name='seg_1')
chain = Ocd_Chain(name='chain_1')
chain.addSegment(seg)
chain.addJoint(seg)

chain.initJoints()