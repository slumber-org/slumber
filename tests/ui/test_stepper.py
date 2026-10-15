"""Tests for the stepper's step state and availability rules."""

from __future__ import annotations

from slumber.ui.layouts.stepper import StepperProgress


class TestStatus:
    def test_first_step_is_current_and_the_rest_pending(self) -> None:
        progress = StepperProgress(3)
        assert [progress.status(i) for i in range(3)] == [
            "current",
            "pending",
            "pending",
        ]

    def test_finished_step_is_done_once_left(self) -> None:
        progress = StepperProgress(2)
        progress.mark_done(0)
        assert progress.go_to(1)
        assert progress.status(0) == "done"
        assert progress.status(1) == "current"

    def test_leaving_an_unfinished_step_leaves_it_pending(self) -> None:
        progress = StepperProgress(2)
        progress.mark_done(0)
        progress.go_to(1)
        progress.go_to(0)
        assert progress.status(1) == "pending"


class TestAvailability:
    def test_only_the_gate_and_earlier_steps_are_available(self) -> None:
        progress = StepperProgress(3)
        assert [progress.is_available(i) for i in range(3)] == [True, False, False]
        progress.mark_done(0)
        assert [progress.is_available(i) for i in range(3)] == [True, True, False]

    def test_everything_is_available_once_every_step_is_done(self) -> None:
        progress = StepperProgress(3)
        for index in range(3):
            progress.mark_done(index)
        assert all(progress.is_available(i) for i in range(3))

    def test_everything_is_available_with_allow_skip(self) -> None:
        progress = StepperProgress(3, allow_skip=True)
        assert all(progress.is_available(i) for i in range(3))

    def test_out_of_range_step_is_unavailable(self) -> None:
        progress = StepperProgress(2, allow_skip=True)
        assert not progress.is_available(2)
        assert not progress.is_available(-1)

    def test_availability_follows_the_statuses(self) -> None:
        progress = StepperProgress(3)
        progress.mark_done(0)
        assert not progress.is_available(2)
        progress.mark_done(1)
        assert progress.is_available(2)


class TestNavigation:
    def test_go_to_refuses_an_unavailable_step(self) -> None:
        progress = StepperProgress(2)
        assert not progress.go_to(1)
        assert progress.current == 0

    def test_go_to_the_current_step_does_nothing(self) -> None:
        progress = StepperProgress(2, allow_skip=True)
        assert not progress.go_to(0)
        assert progress.status(0) == "current"

    def test_go_to_moves_to_an_available_step(self) -> None:
        progress = StepperProgress(3, allow_skip=True)
        assert progress.go_to(2)
        assert progress.current == 2

    def test_is_last(self) -> None:
        progress = StepperProgress(2, allow_skip=True)
        assert not progress.is_last
        progress.go_to(1)
        assert progress.is_last


class TestCompletion:
    def test_cannot_complete_while_a_step_is_unfinished(self) -> None:
        progress = StepperProgress(2)
        progress.mark_done(0)
        assert not progress.can_complete()

    def test_can_complete_when_every_step_is_done(self) -> None:
        progress = StepperProgress(2)
        progress.mark_done(0)
        progress.mark_done(1)
        assert progress.can_complete()

    def test_can_complete_with_allow_skip(self) -> None:
        assert StepperProgress(2, allow_skip=True).can_complete()
