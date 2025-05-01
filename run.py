import threading
import asyncio
from youtubezeno import SEA, start_streaming

async def main():
    room_id = "6706b1dc20084804ef575ccb"
    token = "1aa3bc4cdf336f0f398b2525ec02e70dedc5b0a0efdbfa2d8d334bfdc92aa107"    
    bot_instance = SEA()  
    # Start the streaming thread
    streaming_thread = threading.Thread(target=start_streaming, args=(bot_instance,))
    streaming_thread.daemon = True
    streaming_thread.start()
    while True:
        try:
            await asyncio.sleep(5)
            await bot_instance.run(room_id, token)
        except Exception as e:
            print(f"Bot error: {e}. Restarting in 5 seconds...")
            await asyncio.sleep(5)
if __name__ == '__main__':
    asyncio.run(main())
