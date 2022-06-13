import yaml
import re

def check_config_ssh(ssh):
    if not (ssh and isinstance(ssh, dict)):
        print("<ssh> configure error")
        return False

    host = ssh.get("host", None)
    if not (host and isinstance(host, str)):
        return False

    user = ssh.get("user", None)
    if not (user and isinstance(user, str)):
        return False

    passwd = ssh.get("passwd", None)
    if not (passwd and isinstance(passwd, str)):
        return False

    return True


def check_config_grpc(grpc):
    if not (grpc and isinstance(grpc, dict)):
        print("You must specify grpc as a dictinary")
        return False

    host = grpc.get("host", None)
    if not (host and isinstance(host, str)):
        print("You must specify grpc[host] as a string")
        return False

    auth = grpc.get("auth", None)
    if not auth:
        return True

    if not isinstance(auth, dict):
        return False

    s_key = auth.get("server_key", None)
    s_crt = auth.get("server_cert", None)
    c_crt = auth.get("client_cert", None)
    if not (s_key and isinstance(s_key, str)):
        print("Your must specify server_key as a string")
        return False

    if not (s_crt and isinstance(s_crt, str)):
        print("Your must specify server_cert as a string")
        return False

    if not (s_crt and isinstance(s_crt, str)):
        print("Your must specify client_cert as a string")
        return False

    if not (s_key.startswith("/") and s_crt.startswith("/") and c_crt.startswith("/")):
        print("server_key & server_cert & client_cert : must be absolute path")
        return False

    return True


def check_config_versions(versions):
    if not (versions and isinstance(versions, list)):
        print("You must specify versions as a list")
        return False

    if len(versions) < 1:
        print("You must specify at least 1 version")
        return False

    for ver in versions:
        if not isinstance(ver, str):
            print("You must specify version as a string")
            return False

        if not re.match(r"v[0-9]{2}\.[0-9]{2}", ver):
            print("You must specify version as format 'v22.03'")
            return False
        if ver < "v21.08":
            print("You must specify version newer than 'v21.05'")
            return False
    return True


def check_config_pcis(pcis):
    if not (pcis and isinstance(pcis, list)):
        print("You must specify pcis as a list")
        return False

    pci_addrs = []
    pci_re = r"[0-9a-fA-F]{4}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\.[0-9a-fA-F]"
    for pci in pcis:
        pci_addr = pci.get("pci", None)
        pci_addrs.append(pci_addr)

        if not (pci_addr and isinstance(pci_addr, str)):
            print("You must specify pci's address as a string")
            return False

        if not re.match(pci_re, pci_addr):
            print("%s Format of the pci address must be xxxx:xx:xx.x" % pci_addr)
            return False

        mode = pci.get("mode", None)
        if not (mode and isinstance(mode, str)):
            print("You must specify pci's mode")
            return False

        if mode not in ("dcf", "kernel"):
            print("You must specify pci's mode as 'dcf' or 'kernel'")
            return False

    if len(pcis) != len(set(pci_addrs)):
        print("Can not specify the same pci address")
        return False

    return True


def check_config(cfg):
    ## user & passwd
    if not check_config_ssh(cfg.get("ssh", None)):
        return False

    if not check_config_grpc(cfg.get("grpc", None)):
        return False

    if not check_config_pcis(cfg.get("pcis", None)):
        return False

    if not check_config_versions(cfg.get("versions", None)):
        return False

    return True


def init_config():
    conf_txt = ""
    with open("config.yaml", "r", encoding="utf-8") as f:
        conf_txt = f.read()

    cfg = yaml.safe_load(conf_txt)
    if not check_config(cfg):
        return None
    return cfg
