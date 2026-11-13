from __future__ import annotations

from typing import Any
import httpx
from app.config import settings

class SupabaseRestError(RuntimeError):
    pass

class SupabaseRestClient:
    """Small PostgREST client. User operations use the caller JWT and therefore RLS."""

    def __init__(self, access_token: str | None = None, *, service_role: bool = False) -> None:
        if not settings.supabase_url:
            raise SupabaseRestError("SUPABASE_URL is not configured")
        if service_role:
            if not settings.supabase_service_role_key:
                raise SupabaseRestError("SUPABASE_SERVICE_ROLE_KEY is not configured on the API server")
            api_key = settings.supabase_service_role_key
            bearer = settings.supabase_service_role_key
        else:
            if not settings.supabase_anon_key:
                raise SupabaseRestError("SUPABASE_ANON_KEY is not configured")
            api_key = settings.supabase_anon_key
            bearer = access_token or settings.supabase_anon_key
        self.base_url = settings.supabase_url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json",
        }

    async def request(
        self,
        method: str,
        table: str,
        *,
        params: dict[str, str] | None = None,
        payload: Any = None,
        prefer: str | None = None,
    ) -> Any:
        headers = dict(self.headers)
        if prefer:
            headers["Prefer"] = prefer
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method, f"{self.base_url}/{table}", headers=headers,
                params=params, json=payload,
            )
        if response.is_error:
            detail = response.text[:500]
            raise SupabaseRestError(f"Supabase {method} {table} failed ({response.status_code}): {detail}")
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        result = await self.request("GET", table, params=params)
        return result if isinstance(result, list) else []

    async def select_all(
        self, table: str, params: dict[str, str], *, page_size: int = 1000, max_rows: int = 10000
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        while offset < max_rows:
            page = await self.select(table, {
                **params, "limit": str(min(page_size, max_rows - offset)), "offset": str(offset),
            })
            rows.extend(page)
            if len(page) < page_size:
                break
            offset += len(page)
        return rows

    async def insert(self, table: str, payload: dict[str, Any] | list[dict[str, Any]]) -> Any:
        return await self.request("POST", table, payload=payload, prefer="return=representation")

    async def upsert(self, table: str, payload: list[dict[str, Any]], on_conflict: str) -> None:
        for offset in range(0, len(payload), 500):
            await self.request(
                "POST", table, params={"on_conflict": on_conflict},
                payload=payload[offset:offset + 500],
                prefer="resolution=merge-duplicates,return=minimal",
            )
