"""Environment-driven settings. Loaded once; injected wherever needed."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Brand / persona
    brand_name: str = "Acme"
    agent_name: str = "سارة"
    agent_voice: str = "ar-EG-SalmaNeural"

    # ── LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-4-5-20251001"

    # ── STT
    stt_provider: Literal["deepgram", "azure"] = "deepgram"
    deepgram_api_key: str = ""

    # ── TTS
    tts_provider: Literal["azure", "elevenlabs"] = "azure"
    azure_speech_key: str = ""
    azure_speech_region: str = "westeurope"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # ── Telephony
    telephony_provider: Literal["twilio", "livekit_sip"] = "twilio"

    # Twilio (default, Tier 1)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    public_base_url: str = ""

    # LiveKit SIP (Tier 2 / Tier 3 — populated during migration)
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    sip_trunk_id: str = ""
    sip_outbound_address: str = ""
    sip_outbound_username: str = ""
    sip_outbound_password: str = ""
    ntra_license_number: str = ""

    # ── CRM
    crm_sink: Literal["sheets", "hubspot", "webhook"] = "sheets"
    google_service_account_json: str = ""
    google_sheet_id: str = ""
    google_sheet_tab: str = "Leads"
    hubspot_access_token: str = ""
    crm_webhook_url: str = ""
    calendly_webhook_url: str = ""
    human_handoff_number: str = ""

    # ── Telemetry
    telemetry_path: Path = Field(default=Path("data/calls.jsonl"))

    # ── Outbound dialing
    dnc_path: Path | None = None
    outbound_api_key: str = ""

    # ── Server
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"

    @property
    def prompts_dir(self) -> Path:
        """Directory containing prompt markdown files. Repo-root `prompts/`."""
        return Path(__file__).resolve().parents[2] / "prompts"


settings = Settings()
