"""Settings for nicegui2 backend validation from YAML."""

from __future__ import annotations

from pydantic import BaseModel, Field

from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.pages.welcome.settings import WelcomeSettings
from slumber.plugins.ui.nicegui2.pages.farewell.settings import FarewellSettings


class NiceGUI2Settings(BaseModel):
    """Top-level settings for the nicegui2 backend."""

    port: int = Field(default=8080, ge=1, le=65535)
    show: bool = Field(default=True)
    shell: ShellSettings = Field(default_factory=ShellSettings)
    welcome: WelcomeSettings = Field(default_factory=WelcomeSettings)
    farewell: FarewellSettings = Field(default_factory=FarewellSettings)
