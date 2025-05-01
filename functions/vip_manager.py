from .vip_data import save_vip_list  # import save function

OWNER_USERNAME = "raybm"

def is_vip(username: str, vip_list: set) -> bool:
    return username == OWNER_USERNAME or username in vip_list
    
def get_vip_list(vip_list: set) -> str:
    if not vip_list:
        return "VIP list is empty."
    return "VIPs:\n" + "\n".join(f"- {vip}" for vip in sorted(vip_list))
    
async def handle_vip_command(user, message: str, vip_list: set) -> str:
    username = user.username.lower()
    
    if username != OWNER_USERNAME:
        return f"Sorry {user.username}, only the bot owner can manage VIPs."

    if message.lower().startswith("vip@"):
        target_username = message.split("@", 1)[1].strip().lower()
        if not target_username:
            return "Please specify a username to add as VIP."
        if target_username in vip_list:
            return f"{target_username} is already a VIP."
        vip_list.add(target_username)
        save_vip_list(vip_list)  # Save after adding
        return f"✅ {target_username} has been added to the VIP list."

    if message.lower().startswith("unvip@"):
        target_username = message.split("@", 1)[1].strip().lower()
        if not target_username:
            return "Please specify a username to remove from VIP."
        if target_username not in vip_list:
            return f"{target_username} is not in the VIP list."
        vip_list.remove(target_username)
        save_vip_list(vip_list)  # Save after removing
        return f"❌ {target_username} has been removed from the VIP list."

    return "Invalid VIP command format. Use vip@username or unvip@username."
