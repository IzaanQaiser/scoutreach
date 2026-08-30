from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TopStartupsStage = Literal[
    "Pre-Seed",
    "Seed",
    "Series A",
    "Series B",
    "Series C",
    "Series D",
    "Series E",
    "Series F",
    "Series G",
    "Post-IPO",
]


class TopStartupsCompany(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    website: str
    domain: str
    description: str | None = None
    categories: list[str] = Field(default_factory=list)
    location: str | None = None
    stage: TopStartupsStage | None = None
    funding_text: str | None = None
    source_url: str
