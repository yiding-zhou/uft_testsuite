import core

disable_docker = True

def run():
    count = 1 // len(core.ports_configured()) + 1
    for _ in range(0, count):
        if not core.restart_uft():
            return False

    return True
