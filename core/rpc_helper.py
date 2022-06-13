import grpc

from flow_pb2_grpc import FlowServiceStub
from flow_pb2 import *


'''
class FlowCodeGenerator:
    def __init__(self):
        pass

    def header_gen(self, server_addr="localhost:50051", cert=None):
        if cert:
            res = "with open(cert,'rb') as f:\n"
            res += "    creds = grpc.ssl_channel_credentials(f.read())\n"
            res += "channel = grpc.secure_channel(server_addr, creds)\n"
        else:
            res = "channel = grpc.insecure_channel(%s)\n" % server_addr

        res += "flow_stub = FlowServiceStub(channel)\n"
        return res

    def _port_request_codegen(self, cmd, port_id):
        res = "req = RequestofPort()\n"
        res += "req.port_id = %s\n" %  port_id
        res += "flow_stub.%s(req)\n" % cmd
        return res

    def _vc_request_codegen(self, cmd, port_id, patterns, actions):
        res = "req = RequestFlowCreate()\n"
        res += "req.attr.ingress = 1\n"
        res += "req.port_id = %d\n" % port_id

        for i,p in enumerate(patterns):
            res += flow_pattern_codegen(patterns)
            res += "req.pattern.append(item)\n"

        for i,a in enumerate(actions):
            res += "action = rte_flow_action()\n"
            action_func = action_func_map.get(a.action, None) 
            if action_func is None:
                raise Exception('Unsupport action %s' % a.action)
            
            if a.action == 'queue':
                print('a.prep = ',a.prep)
            action.type = action_func[0]
            if action_func[1] is not None:
                action_struct = action_func[1]()
                if a.prep:
                    setattr(action_struct, a.prep, parse_int(a.val))
                action.conf.Pack(action_struct)
            req.action.append(action)
            
        action_end = rte_flow_action()
        action_end.type = RTE_FLOW_ACTION_TYPE_END
        req.action.append(action_end)
        
        return getattr(self.flow_stub, cmd)(req)

    def list_codegen(self, port_id):
        return self._port_request_codegen('List', port_id)

    def flush_codegen(self,port_id):
        return self._port_request_codegen('Flush', port_id)

    def destroy_codegen(self, port_id, flow_id):
        return self._flow_request_codegen('Destroy', port_id, flow_id)

    def query_codegen(self, port_id , flow_id):
        return self._flow_request_codegen('Query', port_id, flow_id)

    def _flow_request_codegen(self, cmd, port_id, flow_id):
        res = "req = RequestFlowofPort()\r\n"
        res += "req.port_id = %d\r\n" % port_id
        res += "req.flow_id = %d\r\n" % flow_id
        res += "flow_stub.%s(req)" % cmd
        return res

    def listports_codegen(self):
        return "flow_stub.ListPorts(RequestListPorts())\r\n"

def flow_pattern_codegen(pattern):
    try:
        helper = pattern_helper.get(pattern.name)
        res = "item = rte_flow_item()\r\n"
        res += "item.type = %d\r\n" % helper[0]
        res += "mask = %s()\r\n" % helper[1].__class__.__name__
        res += "spec = %s()\r\n" % helper[1].__class__.__name__
        res += "last = %s()\r\n" % helper[1].__class__.__name__
    
        normal_fields,range_fields = flow_handle_fields(pattern)
        for fname,(fprep,fval)  in normal_fields.items():
            detail = helper[2][fname]
            detail_str = ''
            for d in detail[0][:-1]:
                detail_str += '.%s' % d
            detail_str += ".%s" % detail[0][-1]
            val = detail[1](fval)
            res += "mask%s = %d\r\n" % val
            if val != detail[2] and fprep == 'is':
                res += "spec%s = %d\r\n" % detail[3]
    
        for k,v in range_fields.items():
            for kk,vv in v.items():
    
                detail = helper[2][kk]
                detail_str = ''
                for d in detail[0][:-1]:
                    detail_str += ".%s" % d
                
                val = detail[1](vv)
                res += k + detail_str + " = %d\r\n" % val
    
        if normal_fields:
            res += "item.spec.Pack(mask)\r\n"
            res += "item.mask.Pack(spec)\r\n"
    
        if 'last' in range_fields:
            res += "item.spec.Pack(last)\r\n"

        return res
    except Exception as e:
        print(e)
'''


class FlowBuilder(object):
    def __init__(self, server_addr=None, cert=None):
        self.flow_stub = None
        channel = None
        if not server_addr:
            server_addr = "localhost:50051"
        if cert:
            with open(cert, 'rb') as f:
                creds = grpc.ssl_channel_credentials(f.read())
            channel = grpc.secure_channel(server_addr, creds)
        else:
            channel = grpc.insecure_channel(server_addr)
        self.flow_stub = FlowServiceStub(channel)

    ## create or validate
    def create(self, port_id, patterns, actions):
        return self._vc_request('Create', port_id, patterns, actions)

    def validate(self, port_id, patterns, actions):
        return self._vc_request('Validate', port_id, patterns, actions)

    def _vc_request(self, cmd, port_id, patterns, actions):
        req = RequestFlowCreate()
        req.attr.ingress = 1
        req.port_id = int(port_id)

        for i, p in enumerate(patterns):
            item = flow_pattern_item(p)
            req.pattern.append(item)

        item = rte_flow_item()
        item.type = RTE_FLOW_ITEM_TYPE_END
        req.pattern.append(item)

        for i, a in enumerate(actions):
            action = rte_flow_action()

            action_func = action_func_map.get(a.action, None)
            if action_func is None:
                raise Exception('Unsupport action %s' % a.action)

            if a.action == 'queue':
                print('a.prep = ', a.prep)
            action.type = action_func[0]
            if action_func[1] is not None:
                action_struct = action_func[1]()
                if a.prep:
                    setattr(action_struct, a.prep, parse_int(a.val))
                action.conf.Pack(action_struct)
            req.action.append(action)

        action_end = rte_flow_action()
        action_end.type = RTE_FLOW_ACTION_TYPE_END
        req.action.append(action_end)

        return getattr(self.flow_stub, cmd)(req)

    # list flush
    def list(self, port_id):
        return self._port_request('List', port_id)

    def flush(self, port_id):
        return self._port_request('Flush', port_id)

    def _port_request(self, cmd, port_id):
        req = RequestofPort()
        req.port_id = port_id
        return getattr(self.flow_stub, cmd)(req)

    # destroy query
    def destroy(self, port_id, flow_id):
        return self._flow_request('Destroy', port_id, flow_id)

    def query(self, port_id, flow_id):
        return self._flow_request('Query', port_id, flow_id)

    def _flow_request(self, cmd, port_id, flow_id):
        req = RequestFlowofPort()
        req.port_id = port_id
        req.flow_id = flow_id
        return getattr(self.flow_stub, cmd)(req)

    # listports
    def listports(self):
        return self.flow_stub.ListPorts(RequestListPorts())

    def error_from_response(self, resp):
        # create validate flush destroy query
        if hasattr(resp, 'error_info'):
            errinfo = getattr(resp, 'error_info')
            typ = getattr(errinfo, 'type')
            if typ != 0:
                return str(errinfo.mesg)  # ,encoding='ascii')
            return None

        elif isinstance(resp, ResponseFlowList):
            return None

        elif isinstance(resp, ResponsePortList):
            return None
        else:
            return "Unkown response"

    def ruleno_from_response(self, resp):
        if not isinstance(resp, ResponseFlowCreate):
            return -1

        return resp.flow_id

    def rules_from_response(self, resp):
        res = []
        if isinstance(resp, ResponseFlowList):
            return res

        resp.results.sort(key=lambda x: x.flow_id)
        for r in resp.results:
            res.append((r.flow_id, r.description))

        return res

    def ports_from_response(self, resp):
        res = []
        if not isinstance(resp, ResponsePortList):
            return res

        resp.ports.sort(key=lambda x: x.port_id)
        for p in resp.ports:
            res.append((p.port_id, p.port_pci, p.port_mode))

        return res


def parse_int(s):
    if s.startswith('0x'):
        return int(s, 16)

    return int(s)


def parse_ipv4(s):
    res = 0
    ibytes = s.split('.')
    for b in ibytes:
        res = (res << 8) + (int(b) & 0xff)
    return res


def parse_ipv6(s):
    res = 0
    ibytes = s.split("::")
    for b in ibytes:
        res = (res << 16) + (int(b) & 0xffff)
    return res


def parse_mac(s):
    return bytes(bytearray.fromhex(s.replace(':', '')))


action_func_map = {
    'drop': (RTE_FLOW_ACTION_TYPE_DROP, None),
    'vf': (RTE_FLOW_ACTION_TYPE_VF, rte_flow_action_vf),
    'mark': (RTE_FLOW_ACTION_TYPE_MARK, rte_flow_action_mark),
    'queue': (RTE_FLOW_ACTION_TYPE_QUEUE, rte_flow_action_queue),
}

eth_field_map = {
    'src': (('src', 'addr_bytes'), parse_mac, b'\x00\x00\x00\x00\x00\x00', b'\xff\xff\xff\xff\xff\xff'),
    'dst': (('dst', 'addr_bytes'), parse_mac, b'\x00\x00\x00\x00\x00\x00', b'\xff\xff\xff\xff\xff\xff'),
    'type': (('type',), parse_int, 0xffff, 0xffff),
}

ipv4_field_map = {
    'src': (('hdr', 'src_addr'), parse_ipv4, 0, 0xffffffff),
    'dst': (('hdr', 'dst_addr'), parse_ipv4, 0, 0xffffffff),
    'tos': (('hdr', 'type_of_service'), parse_int, 0, 0xff),
    'ttl': (('hdr', 'time_to_live'), parse_int, 0, 0xff),
    'proto': (('hdr', 'next_proto_id'), parse_int, 0, 0xff),
}

ipv6_field_map = {
    'src': (('hdr', 'src_addr'), parse_ipv6, 0, 0xffffffffffffffff),
    'dst': (('hdr', 'dst_addr'), parse_ipv6, 0, 0xffffffffffffffff),
    'proto': (('hdr', 'proto'), parse_int, 0, 0xff),
}

tcp_field_map = {
    'src': (('hdr', 'src_port'), parse_int, 0, 0xffff),
    'dst': (('hdr', 'dst_port'), parse_int, 0, 0xffff),
}

udp_field_map = {
    'src': (('hdr', 'src_port'), parse_int, 0, 0xffff),
    'dst': (('hdr', 'dst_port'), parse_int, 0, 0xffff),
}

vlan_field_map = {
    'tci': (('tci',), parse_int, 0, 0xffff),
}

pppoe_proto_id_field_map = {
    'pppoe_proto_id': (('proto_id',), parse_int, 0, 0xffff),
}

pppoe_field_map = {
    'code': (('code',), parse_int, 0, 0xfff),
    'seid': (('session_id',), parse_int, 0, 0xffff),
}

pattern_helper = {
    'eth': (RTE_FLOW_ITEM_TYPE_ETH, rte_flow_item_eth, eth_field_map),
    'ipv4': (RTE_FLOW_ITEM_TYPE_IPV4, rte_flow_item_ipv4, ipv4_field_map),
    'ipv6': (RTE_FLOW_ITEM_TYPE_IPV6, rte_flow_item_ipv4, ipv6_field_map),
    'tcp': (RTE_FLOW_ITEM_TYPE_TCP, rte_flow_item_tcp, tcp_field_map),
    'udp': (RTE_FLOW_ITEM_TYPE_UDP, rte_flow_item_udp, udp_field_map),
    'vlan': (RTE_FLOW_ITEM_TYPE_VLAN, rte_flow_item_vlan, vlan_field_map),
    'pppoes': (RTE_FLOW_ITEM_TYPE_PPPOES, rte_flow_item_pppoe, pppoe_field_map),
    'pppoe_proto_id': (RTE_FLOW_ITEM_TYPE_PPPOE_PROTO_ID, rte_flow_item_pppoe_proto_id, pppoe_proto_id_field_map),
}


def flow_handle_fields(pattern):
    normal_fields = {}
    range_fields = {}
    for f in pattern.fields:
        if f.prep in ('mask', 'last'):
            if not range_fields.get(f.prep, None):
                range_fields[f.prep] = {f.field: f.val}
            else:
                range_fields[f.prep][f.field] = f.val
        else:
            normal_fields[f.field] = (f.prep, f.val)

    if len(range_fields) > 2:
        raise Exception("too much spec/mask/last")

    return normal_fields, range_fields


def flow_pattern_item(pattern):
    helper = pattern_helper.get(pattern.name, None)
    if not helper:
        raise Exception("Unsupported pattern %s" % pattern.name)

    item = rte_flow_item()
    item.type = helper[0]
    subitems = [helper[1]() for i in range(3)]

    normal_fields, range_fields = flow_handle_fields(pattern)
    for fname, (fprep, fval) in normal_fields.items():
        # get actual field
        spec_field = subitems[0]
        mask_field = subitems[1]
        detail = helper[2][fname]

        for d in detail[0][:-1]:
            spec_field = getattr(spec_field, d)
            mask_field = getattr(mask_field, d)

        val = detail[1](fval)
        setattr(spec_field, detail[0][-1], val)

        if val != detail[2] and fprep == 'is':
            setattr(mask_field, detail[0][-1], detail[3])

    for k, v in range_fields.items():
        for kk, vv in v.items():
            field = subitems[1]
            if k == 'last':
                field = subitems[2]

            detail = helper[2][kk]
            for d in detail[0][:-1]:
                field = getattr(field, d)

            val = detail[1](vv)
            setattr(field, detail[0][-1], val)

    if normal_fields:
        item.spec.Pack(subitems[0])
        item.mask.Pack(subitems[1])

    if 'last' in range_fields:
        item.spec.Pack(subitems[2])
    return item
