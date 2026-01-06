import asyncio

async def slow_task():
    try:
        print("task started")
        await asyncio.sleep(65)
        print("task completed")
    finally:
        print("cleanup ran")

async def main():
    try:
        await asyncio.wait_for(slow_task(), timeout=1)
    except asyncio.TimeoutError:
        print("Timed out!")

asyncio.run(main=main())