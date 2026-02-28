import asyncio
from src.main import GameEngine

async def main():
    engine = GameEngine()
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())
