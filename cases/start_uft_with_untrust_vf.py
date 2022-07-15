import core

def run():
    pcis = core.ports_configured()
    intf = pcis[0].get("intf")
    core.stop_uft()
    core.execute_command("ip link set %s vf 0 trust off", intf)
    res = core.restart_uft()
    core.stop_uft()
    core.execute_command("ip link set %s vf 0 trust on", intf)
    return not res