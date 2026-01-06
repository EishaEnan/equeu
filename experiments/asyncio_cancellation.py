import asyncio

async def slow_task():
    try:
        print("task started")
        await asyncio.sleep(60)
        print("task completed")  # should not run
    finally:
        print("cleanup ran")

async def main():
    task = asyncio.create_task(slow_task())
    await asyncio.sleep(1)
    print("cancelling task")
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("task cancelled")

asyncio.run(main())
