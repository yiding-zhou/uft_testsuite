import core

def run(ver):
    for i, pci in enumerate(core.ports_configured(ver)):
        port_id = i
        core.execute_rule("flow flush %d" % port_id)
    cmd = "flow create %d ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id %d / end"
    if core.version_need_represented(ver):
        cmd = "flow create %d ingress pattern eth / ipv4 / udp dst is 4789 / end actions represented_port ethdev_port_id %d / end"

    step = 1
    for i, pci in enumerate(core.ports_configured(ver)):
        port_id = i
        core.insert_log_tag("Step %d : create rule on port %d" % (step, port_id), 1)
        step += 1
        if port_id == 0:
                resp = core.execute_rule(cmd % (port_id, 2))
        else:
                resp = core.execute_rule(cmd % (port_id, 1))
        core.insert_log_tag("Step %d : check rule on port %d" % (step, port_id), 1)
        step += 1
        if 0 != core.ruleno_from_resp(resp):
            return False

    return True
