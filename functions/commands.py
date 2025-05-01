def is_teleport_command(message: str) -> bool:
    return any(message.lower().startswith(prefix) for prefix in ["/tele", "/tp", "/fly", "!tele", "!tp", "!fly"])

async def handle_teleport_command(user, message, send_message):
    # Your teleport logic goes here
    await send_message(f"Teleporting {user.username}... (example)")
