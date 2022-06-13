import core

disable_docker=True

cmd0 = "flow create %d ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.0 / end actions drop / end"
cmd1 = "flow create %d ingress pattern eth / ipv4 src spec 192.168.0.126 src mask 255.255.0.255 / udp / end actions drop / end"
cmd2 = "flow create %d ingress pattern eth / ipv4 / udp src spec 8017 src mask 65520 / end actions drop / end"
cmd3 = "flow create %d ingress pattern eth / ipv4 dst spec 192.168.0.1 dst mask 255.255.255.0 / end actions drop / end"

def run():
    for i, _ in enumerate(core.ports_configured()):
        core.execute_rule("flow flush %d" % i)
        core.execute_rule(cmd0 % i)
        core.execute_rule(cmd1 % i)
        core.execute_rule(cmd2 % i)
        core.execute_rule(cmd3 % i)
        core.execute_rule("flow destroy %d rule 2" % i)
        core.execute_rule("flow flush %d" % i)
        resp = core.execute_rule("flow list %d" % i)
        if 0 != len(core.rules_from_resp(resp)):
            return False

    return True
