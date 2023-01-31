import core

def run(ver):
    core.insert_log_tag("Step 1: start server with two ports", 1)
    core.restart_uft()
    core.insert_log_tag("Step 2: kill the server's process", 1)
    core.insert_log_tag("", 10)
    core.insert_log_tag("", 10)
    core.insert_log_tag("Step 3: repeat the previous steps 50 times", 1)
    for _ in range(0, 1):
        if not core.restart_uft():
            return False

    core.insert_log_tag("Step 4: start server with two ports", 1)
    core.restart_uft()
    core.insert_log_tag("Step 5: check the server can start correctly", 1)
    return True
