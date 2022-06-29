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
import asyncio

async def main():
    osu = bancho.OsuVersion(year= 2022, month= 6, day= 29)
    hwid = bancho.HWIDInfo.generate_random()
    server = bancho.TargetServer.from_base_url("example.server")

    client = bancho.BanchoClient.new(
        username= "Username",
        version= osu,
        hwid= hwid,
        server= server,
    )

    res = await client.connect(
        "Password",
    )

    if res:
        print("Connected!")
        print(client.user_id)
        print(client.protocol_version)
    else:
        print("Failed to connect!")
        print(client.user_id)


if __name__ == "__main__":
    asyncio.run(main())
```
