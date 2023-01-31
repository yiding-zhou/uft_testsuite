import core

def run(ver):
    core.execute_rule("flow flush 0")
    cmd = "flow create 0 ingress pattern eth / ipv4 / udp end / actions vf id 100 / end"
    if core.version_need_represented(ver):
        cmd = "flow create 0 ingress pattern eth / ipv4 / udp end / represented_port ethdev_port_id 100 / end"
    core.insert_log_tag("Step 1: add  invalid SWITCH rules", 1)
    resp = core.execute_rule(cmd)
    core.insert_log_tag("Step 2:check the rules created failed at step 1", 1)
    if not core.error_from_resp(resp):
        return False

    return True
