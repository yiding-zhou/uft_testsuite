import core

def run():
    core.execute_rule("flow flush 0")
    cmd = "flow create 0 ingress pattern eth / ipv4 / udp end actions vf id 100"
    resp = core.execute_rule(cmd)
    if not core.error_from_resp(resp):
        return False

    return True
