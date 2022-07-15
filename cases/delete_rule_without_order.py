import core

cmd0 = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.0 / end actions drop / end"
cmd1 = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.126 src mask 255.255.0.255 / udp / end actions drop / end"
cmd2 = "flow create 0 ingress pattern eth / ipv4 / udp src spec 8017 src mask 65520 / end actions drop / end"
cmd3 = "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.1 dst mask 255.255.255.0 / end actions drop / end"

def run():
    core.execute_rule("flow flush 0")
    core.execute_rule(cmd0)
    core.execute_rule(cmd1)
    core.execute_rule(cmd2)
    core.execute_rule(cmd3)
    core.execute_rule("flow destroy 0 rule 2")
    core.execute_rule("flow flush 0")
    resp = core.execute_rule("flow list 0")
    if 0 != len(core.rules_from_resp(resp)):
        return False

    return True
