import pymel.core as pmc
import maya.OpenMaya as om
import FabricEngine.Core as fabric
import json

opaqueDict = '{"uiHidden" : "","uiOpaque" : "true","uiPersistValue" : "","uiRange" : "","uiHardRange" : "","uiCombo" : ""}'
defaultMat44 = '{\n  "row0" : {\n    "x" : 1,\n    "y" : 0,\n    "z" : 0,\n    "t" : 0\n    },\n  "row1" : {\n    "x" : 0,\n    "y" : 1,\n    "z" : 0,\n    "t" : 0\n    },\n  "row2" : {\n    "x" : 0,\n    "y" : 0,\n    "z" : 1,\n    "t" : 0\n    },\n  "row3" : {\n    "x" : 0,\n    "y" : 0,\n    "z" : 0,\n    "t" : 1\n    }\n  }'

def getPortValue(canvasNode, port):
    # Get Client
    contextID = cmds.fabricSplice('getClientContextID')
    if contextID == '':
        cmds.fabricSplice('constructClient')
        contextID = cmds.fabricSplice('getClientContextID')
    client = fabric.createClient({"contextID": contextID})
    host = client.DFG.host

    # Get Binding for Operator
    opBindingID = cmds.FabricCanvasGetBindingID(n=canvasNode)
    opBinding = host.getBindingForID(opBindingID)

    # force graph evaluation
    opBinding.execute()

    # return port value
    rtVal = opBinding.getArgValue(port)
    return rtVal


class Ocd_Deformer(object):
    def __init__(self, name=''):
        super(Ocd_Deformer, self).__init__()
        self.name=name
        self.chains=[]
        self.bendPushes=[]
        self.cmpPushes=[]
        self.xfoPushes=[]
        self.build()

    def addChain(self, chain):
        '''
        expects an instance of Ocd_Chain passed as 'chain'
        '''
        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.bendPushes)*300+100, y=len(self.bendPushes)*100+100)

        # Create input port and connections (bend)
        bendPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='%s_bends' % chain.name, p='In', ui=opaqueDict, t='Float32[]')
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s=bendPort, d='%s.element' % p)
        pmc.connectAttr('%s.bends' % chain.name, '%s.%s' % (self.cn.getName(), bendPort))
        if self.bendPushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.bendPushes[-1], d='%s.array' % p)
        self.bendPushes.append(p)

        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.cmpPushes)*300+100, y=len(self.cmpPushes)*100+300)

        # Create input port and connections (cmpVecs)
        cmpPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='%s_cmpVecs' % chain.name, p='In', ui=opaqueDict, t='Vec3[]')
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s=cmpPort, d='%s.element' % p)
        pmc.connectAttr('%s.cmpVecs' % chain.name, '%s.%s' % (self.cn.getName(), cmpPort))
        if self.cmpPushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.cmpPushes[-1], d='%s.array' % p)
        self.cmpPushes.append(p)

        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.xfoPushes)*300+100, y=len(self.xfoPushes)*100+500)

        # Create input port and connections (cmpVecs)
        xfoPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='%s_xfos' % chain.name, p='In', ui=opaqueDict, t='Vec3[]')
        pmc.FabricCanvasEditPort(m=self.cn.getName(), e="", n='%s_xfos' % chain.name, d='%s_xfos' % chain.name, t="Xfo[][]")
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s=xfoPort, d='%s.element' % p)
        pmc.connectAttr('%s.xfos' % chain.name, '%s.%s' % (self.cn.getName(), xfoPort))
        if self.xfoPushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.xfoPushes[-1], d='%s.array' % p)
        self.xfoPushes.append(p)

        self.chains.append(chain)

    def build(self):
        # Create canvas node
        self.cn = pmc.createNode('canvasNode', name=self.name)


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
        self.joints=[]
        self.initMatPushes=[]
        self.initMats=[]

        self.build()

    def initJoints(self):
        # set all initMats to identity
        for i in range(len(self.initMats)):
            pmc.FabricCanvasSetPortDefaultValue(m=self.cn.getName(), e='', p='%s.value' % self.initMats[i], t='Mat44',  v=defaultMat44)

        # Get local joint spaces
        initMats = getPortValue(self.cn.getName(), 'localMats')

        # Apply local offsets
        for i in range(len(self.initMats)):
            pmc.FabricCanvasSetPortDefaultValue(m=self.cn.getName(), e='', p='%s.value' % self.initMats[i], t='Mat44',  v=initMats[i].getJSON().getSimpleType())

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

        # Create localMat for new joint
        # This allows a non-straight joint to be initialized with a zero value.
        # When bend is calculated, this local offset is applied to the space in which the bend is computed.
        p = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Core.Array.Push', x=len(self.initMatPushes)*300+300, y=len(self.initMatPushes)*100+300)
        m = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='Fabric.Exts.Math.Constants.Mat44', x=len(self.initMatPushes)*300+100, y=len(self.initMatPushes)*100+300)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.value' % m, d='%s.element' % p)
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % p, d='%s.initMats' % self.chain)
        if self.initMatPushes:
            pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.array' % self.initMatPushes[-1], d='%s.array' % p)
        self.initMatPushes.append(p)
        self.initMats.append(m)

    def build(self):
        # Create canvas node
        self.cn = pmc.createNode('canvasNode', name=self.name)

        # create chain preset and output ports
        self.chain = pmc.FabricCanvasInstPreset(m=self.cn.getName(), e='', p='User.chain', x=500, y=100)
        self.localMatsPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='localMats', p='Out', ui=opaqueDict, t='Mat44[]', c='%s.localMats' % self.chain)
        self.bendsPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='bends', p='Out', t='Float32[]', c='%s.bends' % self.chain)
        self.cmpVecsPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='cmpVecs', p='Out', t='Vec3[]', c='%s.cmpVecs' % self.chain)
        self.xfosPort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='xfos', p='Out', ui=opaqueDict, t='Vec3[]')
        pmc.FabricCanvasEditPort(m=self.cn.getName(), e="", n="xfos", d="xfos", t="Xfo[][]")
        pmc.FabricCanvasConnect(m=self.cn.getName(), e='', s='%s.xfos' % self.chain, d=self.xfosPort)
        self.basePort = pmc.FabricCanvasAddPort(m=self.cn.getName(), e='', d='base_matrix', p='In', t='Mat44', c='%s.baseMat' % self.chain)

'''
seg = Ocd_Segment(ctrls=pmc.selected(type='transform'), name='seg_2')
chain = Ocd_Chain(name='chain_1')
chain.addSegment(seg)
chain.addJoint(seg)
d = Ocd_Deformer(name='ocdDef_1')
d.addChain(chain)

chain.initJoints()

x = getPortValue('chain_1', 'bends')
x[1]
y = x[0].getJSON().getSimpleType()
y
type(json.loads(y))