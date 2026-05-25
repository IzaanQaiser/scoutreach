"""Supabase client setup for backend services."""

from __future__ import annotations

from supabase import Client, create_client

from app.utils.settings import Settings


def build_supabase_client(settings: Settings) -> Client:
    """Create the shared Supabase service-role client."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
