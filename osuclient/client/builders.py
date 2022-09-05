from osuclient.packets.constants import PacketID
from osuclient.packets import rw

def send_message_packet(
    content: str,
    target: str,
) -> bytes:
    return (
        rw.PacketWriter()
            .write_str("")
            .write_str(content)
            .write_str(target)
            .finish(PacketID.OSU_SEND_PUBLIC_MESSAGE)
    )

def send_private_message_packet(
    content: str,
    target: str,
) -> bytes:
    return (
        rw.PacketWriter()
            .write_str("")
            .write_str(content)
            .write_str(target)
            .finish(PacketID.OSU_SEND_PRIVATE_MESSAGE)
    )

def start_spectating(
    user_id: int
) -> bytes:
    return (
        rw.PacketWriter()
            .write_i32(user_id)
            .finish(PacketID.OSU_START_SPECTATING)
    )
