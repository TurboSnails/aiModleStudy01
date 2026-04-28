"""数据库初始化脚本"""
import asyncio


async def main():
    from aiModelStudy01.infrastructure import init_db, close_db, get_settings

    print("初始化数据库...")
    await init_db()
    print("✅ 数据库初始化完成")
    print(f"   - 数据库: {get_settings().database_url}")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())