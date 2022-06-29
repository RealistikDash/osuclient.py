from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
    Union,
    Optional,
)
import aiohttp
import random

from osuclient.packets.constants import PacketID
from osuclient.utils import hashes
from . import exceptions
from . import constants

ByteLike = Union[bytes, bytearray]

@dataclass
class BanchoSession:
    """A class representing an active session to bancho."""

    token: str
    url: str
    http: aiohttp.ClientSession

    async def send(self, packet: ByteLike) -> bytes:
        """Sends a written packet buffer to bancho, returning the
        server's response."""

        if self.token == "no" or not self.token:
            raise exceptions.InvalidBanchoTokenException(
                "No bancho session token provided."
            )

        async with self.http.post(self.url, data=packet, headers= {
            "osu-token": self.token,
        }) as response:
            if response.status != 200:
                raise exceptions.InvalidBanchoResponse(
                    f"Bancho responded with status code {response.status} "
                    "(expected 200)."
                )
            if (token := response.headers.get("cho-token")) \
                and token != "no":
                self.token = token
            else:
                raise exceptions.RejectedBanchoTokenException
            return await response.read()

@dataclass
class TargetServer:
    """A class representing the domains of the target server."""

    bancho: str
    avatar: str
    osu: str

    @staticmethod
    def from_base_url(base_url: str, https: bool = True) -> "TargetServer":
        """Creates an instance of `TargetServer` from a base URL by appending
        the usual subdomains to it.
        
        Args:
            base_url: The base URL of the target server without the protocol
                and the trailing slash (eg. `ppy.sh`).
            https: Whether to use HTTPS or not.
        """
        prefix = "https://" if https else "http://"
        formattable = prefix + "{}." + base_url + "/"
        return TargetServer(
            bancho=formattable.format("c"),
            avatar=formattable.format("a"),
            osu=formattable.format("osu"),
        )

@dataclass
class OsuVersion:
    """A class representing an osu! client version."""

    year: int
    month: int
    day: int
    stream: Optional[str] = None

    @property
    def version(self) -> str:
        """Returns the version string."""
        
        stream_suffix = self.stream or ""

        return f"b{self.year}{self.month:02d}{self.day:02d}{stream_suffix}"

@dataclass
class HWIDInfo:
    """A class representing the hardware details of the connecting client."""

    utc_offset: int # TODO: Probably move this outside.
    path_md5: str
    adapters: str # Separated by "."
    adapters_md5: str
    uninstall_md5: str
    disk_md5: str

    @staticmethod
    def generate_random() -> "HWIDInfo":
        """Generates a randomised set of HWID."""

        # probably the most detectable part?
        adapters = ".".join(
            hashes.random_string(10) for _ in range(random.randint(1, 4))
        )

        return HWIDInfo(
            utc_offset=random.randint(-12, 12),
            path_md5=hashes.random_md5(),
            adapters=adapters,
            adapters_md5=hashes.md5(adapters),
            uninstall_md5=hashes.random_md5(),
            disk_md5=hashes.random_md5(),
        )

@dataclass
class BanchoClient:
    """A class representing an instance of an osu client."""

    # Credentials
    user_id: int
    username: str
    allow_dms: bool

    # Bancho stuff
    session: Optional[BanchoSession]
    queue: bytearray
    protocol_version: int
    privileges: constants.Privileges
    server: Optional[TargetServer]
    version: Optional[OsuVersion]
    hwid: Optional[HWIDInfo]

    # Server State
    online_presences: ...
    online_stats: ...

    http: Optional[aiohttp.ClientSession]

    # Packet Stuff
    send_timeout: int
    packet_handlers: dict[PacketID, Callable[[bytes], Awaitable]]

    # Private Methods
    def __setup_http(self) -> None:
        """Sets up the aiohttp client session."""
        self.http = aiohttp.ClientSession(
            skip_auto_headers=["User-Agent"],
            headers={"User-Agent": "osu!"}
        )
    
    def __setup_handlers(self) -> None:
        """Sets up the packet handlers"""

        ...
    
    # Properties
    @property
    def connected(self) -> bool:
        """Checks if the client is currently connected to bancho."""
        return self.session is not None and self.user_id > 0
    
    # Public Methods
    def set_hwid(self, hwid: HWIDInfo) -> "BanchoClient":
        """Sets the hardware details of the client."""
        self.hwid = hwid
        return self
    
    def set_version(self, version: OsuVersion) -> "BanchoClient":
        """Sets the version of the client."""
        self.version = version
        return self

    def set_server(self, server: TargetServer) -> "BanchoClient":
        """Sets the target server."""
        self.server = server
        return self

    # Static Methods
    @staticmethod
    def new(
        username: str,
        version: Optional[OsuVersion] = None,
        hwid: Optional[HWIDInfo] = None,
        server: Optional[TargetServer] = None,
        allow_dms: bool = True,
    ) -> "BanchoClient":
        """Creates a new instance of `BanchoClient`."""

        client = BanchoClient(
            user_id=0,
            username=username,
            allow_dms=allow_dms,
            session=None,
            queue=bytearray(),
            protocol_version=0,
            privileges=constants.Privileges(0),
            server=server,
            version=version,
            hwid=hwid,
            online_presences=None,
            online_stats=None,
            http=None,

            send_timeout= 5,
            packet_handlers={},
        )

        client.__setup_http()
        client.__setup_handlers()

        return client
