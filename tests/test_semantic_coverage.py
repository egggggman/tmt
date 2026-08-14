import inspect
from dataclasses import dataclass

import pytest

import tmnt_design_studio.semantic_coverage as semantic_coverage_module
from tmnt_design_studio.semantic_coverage import SemanticCoverage


@dataclass(frozen=True)
class DummySelectionProgram:
    quantity: int


@dataclass(frozen=True)
class DummySelectionInterpretation:
    program: DummySelectionProgram
    coverage: SemanticCoverage


def test_generic_coverage_exists_without_any_action_specific_program():
    coverage = SemanticCoverage(
        payload_executable=True,
        parent_executable=False,
        followup_executable=True,
        limitations=("dummy_parent_not_implemented",),
    )

    assert coverage.payload_executable
    assert not coverage.parent_executable
    assert coverage.followup_executable
    assert not coverage.fully_supported
    assert coverage.limitations == ("dummy_parent_not_implemented",)


def test_non_token_action_can_pair_its_program_with_the_generic_coverage_value():
    result = DummySelectionInterpretation(
        DummySelectionProgram(quantity=2),
        SemanticCoverage(True, True, False, ("dummy_followup_not_implemented",)),
    )

    assert result.program.quantity == 2
    assert result.coverage.payload_executable
    assert result.coverage.parent_executable
    assert not result.coverage.followup_executable
    assert not result.coverage.fully_supported


def test_generic_model_has_no_token_or_interpreter_dependency_and_does_not_introspect_programs():
    source = inspect.getsource(semantic_coverage_module)
    annotations = SemanticCoverage.__annotations__

    assert "Token" not in source
    assert "card_interpreter" not in source
    assert "program" not in annotations
    assert set(annotations) == {
        "payload_executable",
        "parent_executable",
        "followup_executable",
        "limitations",
    }


def test_unsupported_parent_can_never_become_fully_supported():
    coverage = SemanticCoverage(True, False, True, ("dummy_parent_not_implemented",))
    assert not coverage.fully_supported


def test_limitations_are_explicit_unique_nonempty_reasons():
    with pytest.raises(ValueError, match="nonempty strings"):
        SemanticCoverage(False, False, False, ("",))
    with pytest.raises(ValueError, match="unique"):
        SemanticCoverage(False, False, False, ("same", "same"))
