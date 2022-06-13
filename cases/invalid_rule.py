import core

disable_docker=True

def run():
    for i, _ in enumerate(core.ports_configured()):
        core.execute_rule("flow flush %d" % i)
        cmd = "flow create %d ingress pattern eth / ipv4 / udp end actions vf id 3" % (i + 6)
        resp = core.execute_rule(cmd)
        if not core.error_from_resp(resp):
            return False

    return True
