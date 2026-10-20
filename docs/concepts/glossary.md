# Glossary

## Action

Something the [RunEngine](#runengine) does in response to an [event](#event): start a [phase](#phase), start or stop a [pipeline](#pipeline), or end the [run](#run). You list actions under `do:` in a [handler](#handler). See [Run lifecycle](run-lifecycle.md#events-handlers-and-actions).

## Activity

One step the participant sees or does, such as reading instructions, calibrating a device, a behavioural task, or the sleep screen. You list activities in a [phase](#phase) of a condition file and choose each one with `type:`. An activity only reports that it is finished or that something happened; [handlers](#handler) decide what happens next. See [Run lifecycle](run-lifecycle.md#how-activities-signal).

## AppFrame

The window around every screen of a GUI run: a header with the logo, the study title and optionally the current phase's title, the body where the [layout](#layout) goes, and a footer. You configure it under `ui.settings.frame` in `study.yaml`. See the [UI reference](../reference/ui.md).

## Condition

One version of the study protocol, for example *active* versus *control*. Each condition is one YAML file in `conditions/`, and each [run](#run) carries out one condition. See [Writing conditions](../user-guide/writing-conditions.md).

## Entry phase

The [phase](#phase) a run starts in. You set it with `entry:` at the top of a condition file. See the [Configuration reference](../reference/configuration.md#condition-file-per-condition-yaml).

## Event

A signal that something happened during a run, such as "this phase is completed" (`phase_completed`) or "the participant pressed I'm Awake" (`marked_awake`). Events come from [layouts](#layout) and [activities](#activity), and [handlers](#handler) react to them. See [Run lifecycle](run-lifecycle.md#events-handlers-and-actions).

## Extension

An optional package you install to add features to SLUMBER, for example support for a device or audio playback. An extension can add [plugins](#plugin) and commands. See the [Plugin reference](../reference/plugins.md).

## Handler

A rule that says what happens when an [event](#event) occurs. You write handlers under `on:` on a [phase](#phase) or an [activity](#activity) in a condition file, and list the [actions](#action) to carry out under `do:`. See [Run lifecycle](run-lifecycle.md#events-handlers-and-actions).

## Layout

How a [phase](#phase) arranges its [activities](#activity) on screen. You choose `stepper` or `hub` with `layout:` on each phase. See the [UI reference](../reference/ui.md#layouts).

## Phase

A stage of the session, such as *setup*, *sleep* or *morning*: a set of [activities](#activity) shown in one [layout](#layout), with [handlers](#handler) that decide what happens next. You list phases under `phases:` in a condition file. See [Run lifecycle](run-lifecycle.md#starting-a-phase).

## Pipeline

Processing that runs in the background during a run, for example recording from a headband during sleep and analysing the signal. You define pipelines under `pipelines:` in a condition file, as [units](#unit) and the connections between them, and start and stop them with [actions](#action). See the [Configuration reference](../reference/configuration.md#pipeline).

## Placeholder

A name in curly braces, such as `{assets_dir}` or `{run_dir}`, that SLUMBER replaces with a real value. You use placeholders in settings and paths in YAML, for example to point to a file in `assets/`. See [Paths and placeholders](../user-guide/paths-and-placeholders.md).

## Plugin

A building block you choose by name with `type:` in YAML, such as the `instruction` [activity](#activity), the `stepper` [layout](#layout) or a [unit](#unit). Activities and units can also come from [extensions](#extension). See the [Plugin reference](../reference/plugins.md).

## Run

One session of a participant going through a [condition](#condition). Each run gets its own folder under `runs/`, with `run.json`, logs and the data recorded during the run. See [Running a study](../user-guide/running-a-study.md).

## RunEngine

The part of SLUMBER that carries out a [run](#run): it starts the [entry phase](#entry-phase) and carries out [actions](#action) in response to [events](#event) until the run ends. See [Run lifecycle](run-lifecycle.md).

## Study

Everything that belongs to one research study, in one folder: `study.yaml` with the study-wide settings, the [conditions](#condition) in `conditions/`, files such as instruction texts in `assets/`, and the output of every [run](#run) in `runs/`. See [Study setup](../user-guide/study-setup.md).

## UI

How a [run](#run) is presented to the participant. You choose `gui` or `headless` with `ui.type` in `study.yaml`. See the [UI reference](../reference/ui.md).

## Unit

One processing step in a [pipeline](#pipeline), such as reading the signal from a headband, detecting eye movements, scoring sleep stages or saving data to a file. You list units under `units:` in a pipeline and choose each one with `type:`. See the [Configuration reference](../reference/configuration.md#pipeline).
