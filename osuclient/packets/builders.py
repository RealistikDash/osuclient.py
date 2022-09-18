from .rw import PacketWriter
from .constants import PacketID

__all__ = (
    "heartbeat",
    "logout",
)

def heartbeat() -> bytearray:
    """Writes a heartbeat packet."""

    return (
        PacketWriter()
            .finish(PacketID.OSU_HEARTBEAT)
    )

def logout() -> bytearray:
    """Writes a logout packet."""

    return (
        PacketWriter()
            .finish(PacketID.OSU_LOGOUT)
    )

def send_message_packet(
    content: str,
    target: str,
) -> bytes:
    return (
        PacketWriter()
            .write_str("")
            .write_str(content)
            .write_str(target)
            .finish(PacketID.OSU_SEND_PUBLIC_MESSAGE)
    )

def send_private_message_packet(
    content: str,
    target: str,
    sender_id: int
) -> bytes:
    return (
        PacketWriter()
            .write_str("")
            .write_str(content)
            .write_str(target)
            .write_u32(sender_id)
            .finish(PacketID.OSU_SEND_PRIVATE_MESSAGE)
    )

def start_spectating(
    user_id: int
) -> bytes:
    return (
        PacketWriter()
            .write_i32(user_id)
            .finish(PacketID.OSU_START_SPECTATING)
    )

def set_action(
    action_id: int,
    action_text: str ,
    action_md5: str,
    mods: int,
    gamemode: int,
    beatmap_id: int,
) -> bytes:
    return (
        PacketWriter()
            .write_u8(action_id)
            .write_str(action_text)
            .write_str(action_md5)
            .write_u32(mods)
            .write_u8(gamemode)
            .write_i32(beatmap_id)
            .finish(PacketID.OSU_CHANGE_ACTION)
    )

def join_match(
    match_id: int,
    password: str,
) -> bytes:
    return (
        PacketWriter()
            .write_i32(match_id)
            .write_str(password)
            .finish(PacketID.OSU_JOIN_MATCH)
    )

def match_ready() -> bytes:
    return (
        PacketWriter()
            .finish(PacketID.OSU_MATCH_READY)
    )

def match_loaded() -> bytes:
    return (
        PacketWriter()
            .finish(PacketID.OSU_MATCH_LOAD_COMPLETE)
    )

def match_not_ready() -> bytes:
    return (
        PacketWriter()
            .finish(PacketID.OSU_MATCH_UNREADY)
    )

def match_skip_req() -> bytes:
    return (
        PacketWriter()
            .finish(PacketID.OSU_MATCH_SKIP_REQUEST)
    )

def match_player_finished_map() -> bytes:
    return (
        PacketWriter()
            .finish(PacketID.OSU_MATCH_COMPLETE)
    )

def match_leave() -> bytes:
    return (
        PacketWriter()
            .finish(PacketID.OSU_PART_MATCH)
    )

def match_invite(user_id: int) -> bytes:
    return (
        PacketWriter()
            .write_i32(user_id)
            .finish(PacketID.OSU_MATCH_INVITE)
    )
