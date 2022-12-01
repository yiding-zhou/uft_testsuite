import core

cmd = "flow create %d ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 2 / end"

def run():
    for i, _ in enumerate(core.ports_configured()):
        core.execute_rule("flow flush %d" % i)

    step = 1
    for i, _ in enumerate(core.ports_configured()):
        core.insert_log_tag("Step %d : create rule on port %d" % (step, i), 1)
        step += 1
        resp = core.execute_rule(cmd % i)
        core.insert_log_tag("Step %d : check rule on port %d" % (step, i), 1)
        step += 1
        if 0 != core.ruleno_from_resp(resp):
            return False

    return True
