"""
Usage:  python scripts/generate_key.py <consumer_id>
Default consumer_id = 1
"""
import asyncio
import hashlib
import secrets
import sys

import asyncpg


async def main(consumer_id: int) -> None:
    raw_key   = "mk_live_" + secrets.token_urlsafe(24)
    key_prefix = raw_key[:12]
    key_hash  = hashlib.sha256(raw_key.encode()).hexdigest()

    conn = await asyncpg.connect(
        "postgresql://meterly:meterly@localhost:5432/meterly"
    )
    await conn.execute(
        """
        INSERT INTO api_keys (consumer_id, key_hash, key_prefix, status)
        VALUES ($1, $2, $3, 'active')
        """,
        consumer_id,
        key_hash,
        key_prefix,
    )
    await conn.close()

    print(f"\n  Raw key : {raw_key}")
    print(f"  Prefix  : {key_prefix}")
    print(f"  Hash    : {key_hash}")
    print("\n  ⚠️  Copy the raw key now — it is never stored.\n")


if __name__ == "__main__":
    consumer_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(main(consumer_id))