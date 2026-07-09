"""asyncpg connection pool and query helpers for the predictions table."""
import json
import os

import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "")
_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


async def close_pool() -> None:
    if _pool:
        await _pool.close()


async def insert_prediction(
    air_temp: float,
    process_temp: float,
    rotational_speed: int,
    torque: float,
    tool_wear: int,
    product_type: str,
    failure_prob: float,
    predicted_failure: bool,
    failure_modes: dict,
    model_version: str,
) -> int:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO predictions
              (air_temp, process_temp, rotational_speed, torque, tool_wear, product_type,
               failure_prob, predicted_failure, failure_modes, model_version)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
            RETURNING id
            """,
            air_temp, process_temp, rotational_speed, torque, tool_wear, product_type,
            failure_prob, predicted_failure, json.dumps(failure_modes), model_version,
        )
        return row["id"]


async def get_metrics() -> dict:
    async with _pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM predictions")
        rate = await conn.fetchval(
            """
            SELECT COALESCE(AVG(failure_prob), 0)
            FROM predictions
            WHERE timestamp > NOW() - INTERVAL '30 days'
            """
        )
    return {
        "total_predictions": int(total or 0),
        "failure_rate_30d": round(float(rate or 0), 4),
    }


async def check_connection() -> bool:
    try:
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False
