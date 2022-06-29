from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
    Union,
    Optional,
)
import aiohttp
import asyncio
import random

from osuclient.packets.constants import PacketID
from osuclient.utils import hashes
from osuclient.packets.rw import (
    PacketReader,
    PacketWriter,
    ByteLike,
)
from osuclient.packets import builders
from . import exceptions
from . import constants

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
    _packet_handlers: dict[PacketID, Callable[[PacketReader], Awaitable[None]]]
    _loop_task: Optional[asyncio.Task]

    # Private Methods
    def __setup_http(self) -> None:
        """Sets up the aiohttp client session."""
        self.http = aiohttp.ClientSession(
            skip_auto_headers=["User-Agent"],
            headers={"User-Agent": "osu!"}
        )
    
    def __setup_handlers(self) -> None:
        """Sets up the packet handlers"""

        self._packet_handlers |= {
            PacketID.SRV_LOGIN_REPLY: self.__packet_login_reply,
            PacketID.SRV_PROTOCOL_VERSION: self.__packet_protocol_ver,
        }
    async def __handle_response(self, response: bytes) -> None:
        """Handles a response from the server."""

        reader = PacketReader(response)
        for packet_id, packet_len in reader:
            packet_handler = self._packet_handlers.get(packet_id)
            if not packet_handler:
                reader.skip(packet_len)
                continue
            await packet_handler(reader)
    
    async def __ping_loop(self) -> None:
        """A function meant to be ran as a task that sends the buffer at
        regular intervals."""

        while self.connected:
            self.enqueue(builders.heartbeat())
            await self.send()
            await asyncio.sleep(self.send_timeout)
    
    # Packet Handlers
    async def __packet_login_reply(self, reader: PacketReader) -> None:
        """Handles the login reply packet."""

        # The packet contains a userid or error code. We will handle errors
        # later.
        self.user_id = reader.read_i32()
    
    async def __packet_protocol_ver(self, reader: PacketReader) -> None:
        """Updates the protocol version to correspond with the server's."""

        self.protocol_version = reader.read_i32()

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
    
    def set_http(self, http: aiohttp.ClientSession) -> "BanchoClient":
        """Sets the aiohttp client session."""
        self.http = http
        return self
    
    def set_send_interval(self, interval: int) -> "BanchoClient":
        """Sets the interval at which packets are sent (in seconds)."""
        self.send_timeout = interval
        return self

    async def connect(
        self,
        password: str, # TODO: Make an auth module such as `HWIDInfo`.
        passw_md5: bool = False,
    ) -> bool:
        """Attempts to connect to connect to the osu server specified, returning a bool
        of whether it has been successful.
        
        Args:
            password (str): The password of the user.
            passw_md5 (bool): Whether the password is MD5 hashed or not.
        """

        # Verify we are ready to start.
        assert self.server is not None, "You must set the server before connecting."
        assert self.version is not None, "You must set the version before connecting."
        assert self.hwid is not None, "You must set the hwid before connecting."
        assert self.http is not None, "You must set up the HTTP client before connecting."

        # Login uses password md5
        password_md5 = hashes.md5(password) if not passw_md5 else password

        # Form the response out of the details.
        req_body = "\n".join([
            self.username,
            password_md5,
            "|".join([
                self.version.version,
                str(self.hwid.utc_offset),
                "0", # Display city (outdated)
                ":".join([
                    self.hwid.path_md5,
                    self.hwid.adapters,
                    self.hwid.adapters_md5,
                    self.hwid.uninstall_md5,
                    self.hwid.disk_md5,
                ]),
                "1" if self.allow_dms else "0",
            ])
        ])

        # Send the request.
        async with self.http.post(
            self.server.bancho,
            data=req_body.encode("utf-8"),
        ) as response:
            token = response.headers.get("cho-token")
            if token == "no" or token is None:
                return False
            # Read the response.
            response_body = await response.read()
            await self.__handle_response(response_body)

            # Create sesson if we succeeded.
            if self.user_id > 0:
                self.session = BanchoSession(token, self.server.bancho, self.http)
            return self.connected

    def enqueue(self, data: ByteLike) -> None:
        """Manually enqueues a packet to be sent to the server."""
        self.queue.extend(data)
    
    async def send(self) -> None:
        """Sends the entire enqueued buffer to the server."""
        assert self.session is not None, "You must be connected to send packets."

        await self.session.send(self.queue)
        self.queue.clear()
    
    def start_loop(self) -> asyncio.Task:
        """Starts the ping loop on a new task."""
        assert self.connected, "You must be connected to start the loop."
        self.loop = asyncio.get_event_loop()
        self._loop_task = self.loop.create_task(self.__ping_loop())
        return self._loop_task
    
    async def logout(self) -> None:
        """Logs the client out.
        
        Note:
            Calling this method sends the remaining contents of the buffer
            to the server.
        """

        assert self.connected, "You must be connected to logout."
        self.enqueue(builders.logout())
        await self.send()

        self.user_id = 0 # self.connected is now False
        self.session = None
    
    async def wait_forever(self) -> None:
        """Waits until the client is disconnected."""
        assert self._loop_task is not None, "You must stuck the loop before running forever."
        await self._loop_task
    
    async def run_forever(self) -> None:
        """Runs a connection loop and waits until a condition is met where
        it finishes."""

        # Start the loop.
        self.start_loop()

        # Wait until we are disconnected.
        await self.wait_forever()

    # async def get_latest_osu(self) -> None:
    #    """Sets the osu client to the latest version on peppy's api."""

    # Decorators
    def on_packet(self, packet_id: PacketID) -> Callable:
        """A decorator registering a specific function to a packet handler,
        overriding the default handler."""
        def decorator(func: Callable) -> Callable:
            # TODO: maybe support multiple handlers per packet?
            self._packet_handlers[packet_id] = func
            return func
        return decorator

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
            _packet_handlers={},
            _loop_task=None,
        )

        client.__setup_http()
        client.__setup_handlers()

        return client
