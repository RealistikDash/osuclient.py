from dataclasses import dataclass

from osuclient.packets import rw
from .constants import Privileges

@dataclass
class PlayerPresence:
    id: int
    name: str
    time_offset: int
    country: int
    bancho_priv: Privileges
    lat: float
    lon: float
    rank: int

    @staticmethod
    def from_reader(reader: rw.PacketReader) -> "PlayerPresence":
        return PlayerPresence(
            id= reader.read_i32(),
            name= reader.read_str(),
            time_offset= reader.read_u8() - 24,
            country= reader.read_u8(),
            bancho_priv= Privileges(reader.read_u8()),
            lat= reader.read_f32(),
            lon= reader.read_f32(),
            rank= reader.read_i32(),
        )
