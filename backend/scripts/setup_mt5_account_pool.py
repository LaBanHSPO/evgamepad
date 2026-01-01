"""Populate MT5 account pool from manual provisioning.

Usage:
    python scripts/setup_mt5_account_pool.py --accounts accounts.json

accounts.json format:
[
    {
        "login": 12345678,
        "password": "demo_password",
        "server": "BrokerName-Demo",
        "expiry_date": "2025-06-30"
    }
]
"""
import asyncio
import asyncpg
import json
import sys
from cryptography.fernet import Fernet
from pathlib import Path

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import config


async def populate_account_pool(accounts_file: str):
    """Insert accounts into pool with encryption."""

    # Load accounts
    with open(accounts_file, 'r') as f:
        accounts = json.load(f)

    print(f"Found {len(accounts)} accounts to provision")

    # Initialize encryption
    encryption_key = config.MT5_ENCRYPTION_KEY
    if not encryption_key:
        print("ERROR: MT5_ENCRYPTION_KEY not set in .env")
        print("Generate key: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        return

    cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    # Connect to database
    conn = await asyncpg.connect(
        host=config.POSTGRES_HOST,
        database=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
        port=config.POSTGRES_PORT
    )

    try:
        inserted = 0
        for account in accounts:
            # Encrypt password
            encrypted_password = cipher.encrypt(account['password'].encode()).decode()

            # Insert
            await conn.execute("""
                INSERT INTO mt5_account_pool (
                    account_number, encrypted_password, broker_server,
                    expiry_date, status, health_status
                ) VALUES ($1, $2, $3, $4, 'available', 'healthy')
                ON CONFLICT (account_number) DO UPDATE
                SET encrypted_password = EXCLUDED.encrypted_password,
                    broker_server = EXCLUDED.broker_server,
                    expiry_date = EXCLUDED.expiry_date
            """, account['login'], encrypted_password, account['server'],
                 account.get('expiry_date'))

            print(f"✓ Provisioned account {account['login']}")
            inserted += 1

        print(f"\nSuccessfully provisioned {inserted} accounts")

        # Show pool stats
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'available') as available
            FROM mt5_account_pool
        """)
        print(f"Pool stats: {stats['total']} total, {stats['available']} available")

    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != '--accounts':
        print(__doc__)
        sys.exit(1)

    asyncio.run(populate_account_pool(sys.argv[2]))
