import json
import os

VIP_FILE = "vip_list.json"

def load_vip_list():
    if not os.path.exists(VIP_FILE):
        return set()
    with open(VIP_FILE, "r") as f:
        # Load as a set directly
        return set(json.load(f))

def save_vip_list(vip_list):
    # Ensure the list is sorted before saving (but convert back to a list)
    with open(VIP_FILE, "w") as f:
        json.dump(sorted(list(vip_list)), f)
