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
