import core

need_restart = True

def run():
    res = False
    pcis = core.ports_configured()
    intf = pcis[0].get("intf")
    core.stop_uft()
    core.insert_log_tag("Step 1: set the vf trust off", 1)
    core.insert_log_tag("ip link set %s vf 0 trust off" % intf)
    try:
        core.execute_command("ip link set %s vf 0 trust off" % intf)

        core.insert_log_tag("Step 2: start the container with the untrust vf port", 1)
        res = not core.restart_uft()
        core.insert_log_tag("Step 3: check the server start failed", 1)
        core.stop_uft()
    finally:
        core.execute_command("ip link set %s vf 0 trust on" % intf)
    return res