import core

cmd = "flow create %d ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 2 / end"

def run():
    for i, _ in enumerate(core.ports_configured()):
        core.execute_rule("flow flush %d" % i)
        resp = core.execute_rule(cmd % i)
        if 0 != core.ruleno_from_resp(resp):
            return False

    return True
