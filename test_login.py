import asyncio
import traceback

from app.client import UrjaClient


async def main():
    client = UrjaClient()

    try:
        print("=" * 80)
        print("STEP 1: LOGIN")
        print("=" * 80)

        ok = await client.login()

        print("Login Result :", ok)
        print("Cookies      :", dict(client.client.cookies))

        if not ok:
            print("\nLogin failed.")
            return

        print("\n" + "=" * 80)
        print("STEP 2: TEST /portal/meters/search")
        print("=" * 80)

        response = await client.client.get(
            "https://urja-ops.flockenergy.tech/portal/meters/search?q=&page=1"
        )

        print("Status :", response.status_code)
        print("URL    :", response.request.url)
        print("Body   :")
        print(response.text[:1000])

        print("\n" + "=" * 80)
        print("STEP 3: TEST /portal/export")
        print("=" * 80)

        response = await client.client.get(
            "https://urja-ops.flockenergy.tech/portal/export"
        )

        print("Status :", response.status_code)
        print("URL    :", response.request.url)
        print("Headers:")
        print(dict(response.headers))

        print("\nBody:")
        print(response.text[:1000])

        print("\n" + "=" * 80)
        print("STEP 4: FINAL COOKIES")
        print("=" * 80)

        print(dict(client.client.cookies))

    except Exception:
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())