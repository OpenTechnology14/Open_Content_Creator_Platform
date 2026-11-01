"""Strict data contracts shared by the CLI and future desktop/mobile surfaces."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")]
Capability = Literal[
    "account-read",
    "post-text",
    "post-image",
    "post-video",
    "schedule-post",
    "live-stream",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Brand(Contract):
    id: Identifier
    display_name: str = Field(min_length=1, max_length=100)
    logo_path: str = Field(pattern=r"^assets/brands/[A-Za-z0-9_.-]+$")
    website: str = Field(pattern=r"^https://")
    source: str = Field(min_length=1, max_length=300)


class OAuthConfig(Contract):
    authorize_url: str = Field(pattern=r"^https://")
    token_url: str = Field(pattern=r"^https://")
    client_id_env: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,127}$")
    client_secret_env: Optional[str] = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{2,127}$")
    use_pkce: bool = True
    extra_authorize_params: dict[str, str] = Field(default_factory=dict, max_length=8)


class Provider(Contract):
    id: Identifier
    display_name: str = Field(min_length=1, max_length=100)
    adapter: Literal["youtube", "twitch", "x", "discord", "catalog-only"]
    connection_status: Literal["available", "registration-required", "planned"]
    oauth: Optional[OAuthConfig] = None
    capability_scopes: dict[Capability, list[str]]
    setup_url: str = Field(pattern=r"^https://")
    notes: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def valid_connection_contract(self) -> Provider:
        if self.connection_status == "available" and (
            self.oauth is None or self.adapter == "catalog-only"
        ):
            raise ValueError("available providers need OAuth and an implemented adapter")
        if "account-read" not in self.capability_scopes:
            raise ValueError("every provider needs an account-read capability")
        return self


class Destination(Contract):
    provider_id: Identifier
    capabilities: list[Capability] = Field(min_length=1, max_length=8)
    default_visibility: Literal["private", "unlisted", "public"] = "private"
    account_label: str = Field(min_length=1, max_length=100)


class SocialProfile(Contract):
    id: Identifier
    display_name: str = Field(min_length=1, max_length=100)
    kind: Literal["stream", "content", "hybrid"]
    brand_ids: list[Identifier] = Field(min_length=1, max_length=16)
    default_brand_id: Identifier
    show_profile_ids: list[Identifier] = Field(default_factory=list, max_length=64)
    destinations: list[Destination] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def valid_default_brand(self) -> SocialProfile:
        if self.default_brand_id not in self.brand_ids:
            raise ValueError("default brand must appear in brand_ids")
        providers = [item.provider_id for item in self.destinations]
        if len(providers) != len(set(providers)):
            raise ValueError("a profile may define each provider once")
        return self


class Catalog(Contract):
    schema_version: Literal[1]
    brands: list[Brand] = Field(min_length=1, max_length=32)
    providers: list[Provider] = Field(min_length=1, max_length=32)
    profiles: list[SocialProfile] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def valid_references(self) -> Catalog:
        brands = {item.id for item in self.brands}
        providers = {item.id: item for item in self.providers}
        if len(brands) != len(self.brands) or len(providers) != len(self.providers):
            raise ValueError("brand and provider IDs must be unique")
        if len({item.id for item in self.profiles}) != len(self.profiles):
            raise ValueError("social profile IDs must be unique")
        for profile in self.profiles:
            if not set(profile.brand_ids) <= brands:
                raise ValueError("profile references an unknown brand")
            for destination in profile.destinations:
                provider = providers.get(destination.provider_id)
                if provider is None:
                    raise ValueError("profile references an unknown provider")
                if not set(destination.capabilities) <= set(provider.capability_scopes):
                    raise ValueError("profile requests a provider capability that is not declared")
        return self


class OAuthSession(Contract):
    schema_version: Literal[1] = 1
    provider_id: Identifier
    profile_id: Identifier
    capability: Capability
    redirect_uri: str = Field(min_length=1, max_length=500)
    state: str = Field(min_length=32, max_length=256)
    code_verifier: Optional[str] = Field(default=None, min_length=43, max_length=128)
    scopes: list[str] = Field(min_length=1, max_length=32)
    created_at: datetime


class ConnectionRecord(Contract):
    schema_version: Literal[1] = 1
    id: Identifier
    profile_id: Identifier
    provider_id: Identifier
    account_id: str = Field(min_length=1, max_length=200)
    account_name: str = Field(min_length=1, max_length=200)
    scopes: list[str] = Field(min_length=1, max_length=64)
    connected_at: datetime
    verified_at: datetime


class PublishJob(Contract):
    schema_version: Literal[1] = 1
    id: Identifier
    profile_id: Identifier
    provider_id: Identifier
    connection_id: Identifier
    brand_id: Identifier
    capability: Capability
    text: Optional[str] = Field(default=None, max_length=5000)
    media_path: Optional[Path] = None
    visibility: Literal["private", "unlisted", "public"] = "private"
    approved: bool = False
    ai_generated: bool = False
    created_at: datetime

    @model_validator(mode="after")
    def valid_payload(self) -> PublishJob:
        if self.capability == "post-text" and not self.text:
            raise ValueError("text posting needs text")
        if self.capability in ("post-image", "post-video") and self.media_path is None:
            raise ValueError("media posting needs a local file")
        if self.capability == "live-stream" and self.media_path is not None:
            raise ValueError("live preparation does not accept a media file")
        return self
