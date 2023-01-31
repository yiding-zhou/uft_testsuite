import core

def run(ver):
    cmd0 = "flow create 0 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 1 / end"
    cmd1 = "flow create 0 ingress pattern eth / ipv4 / udp dst spec 8010 dst mask 65520 / end actions drop / end"
    cmd2 = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.0 / end actions drop / end"
    if core.version_need_represented(ver):
        cmd0 = "flow create 0 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions represented_port ethdev_port_id 1 / end"
    core.execute_rule("flow flush 0")
    core.insert_log_tag("Step 1: add 3 rules", 1)
    core.execute_rule(cmd0)
    core.execute_rule(cmd1)
    core.execute_rule(cmd2)
    core.insert_log_tag("Step 2: flush all the rule", 1)
    core.execute_rule("flow flush 0")
    core.insert_log_tag("Step 3: add 1 new rule", 1)
    resp = core.execute_rule(cmd0)
    core.insert_log_tag("Step 4: check rule number should be 0", 1)
    if core.ruleno_from_resp(resp) != 0:
        print("resp = ", resp)
        return False

    return True
