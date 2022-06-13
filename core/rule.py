import os
from command import FlowCommand
from parse import Parser
from rpc_helper import FlowBuilder

class rule_context:
    def __init__(self, addr, cert=None):
        self.parser = Parser()
        self.builder = FlowBuilder(addr, cert)
        self.cert = cert

    def execute_rule(self, rule):
        rule = rule.strip()
        if len(rule) < 9:
            return None

        method = "Unkown method"
        cmd = None
        if rule == "listports":
            method = rule
        else:
            if rule[0:4] != "flow":
                return None

            cmd = FlowCommand(rule[4:]) 
            if not cmd.build():
                return None
            method = cmd.command
        func = getattr(self.builder, method)
        if not func:
            return None
            
        if method in ('create','validate'):
            patterns = [self.parser.parse(p) for p in cmd.patterns if p]
            actions  = [self.parser.parse(a) for a in cmd.actions if a]
            resp = func(cmd.port_id,patterns, actions)

        elif method in ('flush','list'):
            resp = func(cmd.port_id)
        
        elif method in ('destroy','query'):
            resp = func(cmd.port_id, cmd.flow_id)
        
        elif method == 'listports':
            resp = func()
    
        return resp

def reset_rule_context(cfg, use_cert=False):
    global rule_ctx
    host = cfg.get("grpc").get("host")
    cert = None
    if use_cert:
        cert = os.path.dirname(os.path.abspath(__file__)) + "/ca.crt"
    rule_ctx = rule_context(host + ":50051", cert)

def execute_rule(s):
    if not isinstance(s, str):
        return False
    print(s)
    return rule_ctx.execute_rule(s)

## return error message or None
def error_from_resp(resp):
    return rule_ctx.builder.error_from_response(resp)

## return rule number (int)
def ruleno_from_resp(resp):
    if error_from_resp(resp):
        return -1
    return rule_ctx.builder.ruleno_from_response(resp)

## return ports list as format [(port_id, pci, mode)]
def ports_from_resp(resp):
    if error_from_resp(resp):
        return []
    return rule_ctx.builder.ports_from_response(resp)

## return rules list as format [(rule_no, rule_description)]
def rules_from_resp(resp):
    if error_from_resp(resp):
        return []
    return rule_ctx.builder.rules_from_response(resp)

__all__ = ["execute_rule",
         "error_from_resp", "ruleno_from_resp", "ports_from_resp", "rules_from_resp"]
