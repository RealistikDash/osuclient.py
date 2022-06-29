# osuclient.py
osuclient.py aims to allow the emulation of the communication between an osu client and server through code.

## Note
Please make sure this is only used on servers which you have explicit permission to do so.
Using this without permission may result in restrictions and bans as it is likely to break the rules there.

## Uses
Having full control over what requests are being sent to a server can be extremely beneficial. It helps with:
- Debugging and testing rare scenarios
- Stress testing/benchmarking specific scenarios/usages
- Creating automated testing suites

## Example
A basic client using osuclient.py would look something like this:
```py
from osuclient.client import bancho
from osuclient.packets import constants
from osuclient.packets import rw
import asyncio

loop = asyncio.get_event_loop()

osu = bancho.OsuVersion(year= 2022, month= 6, day= 29)
hwid = bancho.HWIDInfo.generate_random()
client = bancho.BanchoClient.new(
    version= osu,
    hwid= hwid,
)

# Example custom packet handler.
@client.on_packet(constants.PacketID.SRV_NOTIFICATION)
async def on_notification(packet: rw.PacketReader) -> None:
    print(f"Notification> {packet.read_str()}")

async def main():
    res = await client.connect(
        username= "Username",
        password= "Password",
        server= bancho.TargetServer.from_base_url("server.example"),
    )

    if not res:
        print("Failed to connect.")
        return
    
    print("Successfully connected.")
    print(f"{client.username} ({client.user_id})")
    print(f"Connected from {client.version.version} to {client.server.bancho}"
          f" (v{client.protocol_version})")
    
    await client.run_forever()


if __name__ == "__main__":
    loop.run_until_complete(main())

```
