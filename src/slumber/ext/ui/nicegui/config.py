"""Configuration schema for NiceGUI UI page labels and icons."""

from __future__ import annotations

from pydantic import BaseModel, Field, FilePath


class WelcomePageConfig(BaseModel):
    """Configurable labels for the welcome page."""

    icon: str = Field(default="nights_stay")
    subtitle: str = Field(default="")
    start_button: str = Field(default="Start Session")
    start_icon: str = Field(default="play_arrow")


class SleepPageConfig(BaseModel):
    """Configurable labels for the sleep page."""

    asleep_icon: str = Field(default="nights_stay")
    awake_icon: str = Field(default="wb_twilight")
    asleep_label: str = Field(default="Sleeping")
    awake_label: str = Field(default="Awake")
    asleep_subtitle: str = Field(default="Tap when you wake up")
    awake_subtitle: str = Field(default="Ready when you are")
    sleep_button: str = Field(default="Going to Sleep")
    sleep_button_icon: str = Field(default="bedtime")
    sleep_confirm_title: str = Field(default="Going to Sleep")
    sleep_confirm_message: str = Field(default="Are you ready to go to sleep?")
    wake_button: str = Field(default="I'm Awake")
    wake_button_icon: str = Field(default="wb_sunny")
    wake_confirm_title: str = Field(default="I'm Awake")
    wake_confirm_message: str = Field(default="Are you awake now?")
    end_button: str = Field(default="End Session")
    end_button_icon: str = Field(default="logout")
    end_confirm_title: str = Field(default="End Session")
    end_confirm_message: str = Field(
        default="Are you sure you want to end the session?"
    )


class ProcedurePageConfig(BaseModel):
    """Configurable labels for the procedure page."""

    steps_label: str = Field(default="Steps")
    previous_button: str = Field(default="Previous")
    next_button: str = Field(default="Next")
    complete_button: str = Field(default="Complete")
    mark_done_button: str = Field(default="Mark Done")


class CompletePageConfig(BaseModel):
    """Configurable labels for the completion page."""

    icon: str = Field(default="check_circle")
    title: str = Field(default="Session Complete")
    subtitle: str = Field(default="Thank you for participating")
    close_button: str = Field(default="Close")
    close_icon: str = Field(default="close")


class LoginPageConfig(BaseModel):
    """Configurable labels for the login page."""

    icon: str = Field(default="nights_stay")
    title: str = Field(default="SLUMBER")
    subtitle: str = Field(default="Sign in to continue")
    submit_button: str = Field(default="Sign In")
    submit_icon: str = Field(default="login")


class NiceGUIConfig(BaseModel):
    """Top-level config for the NiceGUI UI backend.

    Populated from ``study.yaml`` under ``ui.config`` when the backend
    is set to ``nicegui``.
    """

    welcome: WelcomePageConfig = Field(default_factory=WelcomePageConfig)
    sleep: SleepPageConfig = Field(default_factory=SleepPageConfig)
    procedure: ProcedurePageConfig = Field(default_factory=ProcedurePageConfig)
    complete: CompletePageConfig = Field(default_factory=CompletePageConfig)
    login: LoginPageConfig = Field(default_factory=LoginPageConfig)
    logo: FilePath | None = Field(
        default=None,
        description="Path to logo image. Falls back to docs/assets/logo.png.",
    )
    favicon: FilePath | None = Field(
        default=None,
        description="Path to favicon image. Falls back to docs/assets/favicon.png.",
    )
