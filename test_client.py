import asyncio
import traceback

from app.client import UrjaClient


async def main():
    client = UrjaClient()

    try:
        print("=" * 60)
        print("Testing UrjaClient")
        print("=" * 60)

        print("\n1. Logging in...")
        await client.login()
        print("✅ Login successful")

        print("\n2. Searching meters...")
        result = await client.search_meters()

        print("\n✅ Search successful")
        print(f"Result type: {type(result)}")

        if isinstance(result, dict):
            print("\nKeys:", list(result.keys()))

            if "total" in result:
                print("Total meters:", result["total"])

            if "data" in result:
                print("Meters returned:", len(result["data"]))

                if result["data"]:
                    print("\nFirst meter:")
                    print(result["data"][0])
        else:
            print(result)

    except Exception as e:
        print("\n❌ ERROR OCCURRED")
        print("-" * 60)
        print(type(e).__name__)
        print(e)
        print("-" * 60)
        traceback.print_exc()

    finally:
        await client.close()
        print("\nHTTP client closed.")


if __name__ == "__main__":
    asyncio.run(main())