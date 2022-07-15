import core

def run():
    for _ in range(0, 50):
        if not core.restart_uft():
            return False

    return True
