"""Tests for editorial edit decision planner."""
import pytest
from app.editorial.edit_decision_planner import EditDecisionPlanner, EditOperation


class TestEditDecisionListCreated:
    def test_planner_empty(self):
        planner = EditDecisionPlanner()
        assert planner.list_operations() == []

    def test_add_operation_success(self):
        planner = EditDecisionPlanner()
        op = EditOperation(
            operation_id="edl_001",
            operation="insert_clip",
            anchor="scene_001",
            mode="ripple",
            apply_performed=False,
            requires_preview=True,
            requires_operator_review=True,
        )
        errs = planner.add_operation(op)
        assert errs == []
        assert len(planner.list_operations()) == 1


class TestOperationsApplyPerformedFalse:
    def test_apply_performed_must_be_false(self):
        planner = EditDecisionPlanner()
        op = EditOperation(
            operation_id="edl_bad",
            operation="insert_clip",
            anchor="s1",
            apply_performed=True,
            requires_operator_review=True,
        )
        errs = planner.add_operation(op)
        assert any("apply_performed must be False" in e for e in errs)

    def test_applied_operation_rejected(self):
        planner = EditDecisionPlanner()
        op = EditOperation(operation_id="e1", operation="insert_clip", anchor="s1", apply_performed=False, requires_operator_review=True)
        assert planner.add_operation(op) == []


class TestOperationsOperatorReviewRequired:
    def test_operator_review_false_rejected(self):
        planner = EditDecisionPlanner()
        op = EditOperation(
            operation_id="e1",
            operation="insert_clip",
            anchor="s1",
            apply_performed=False,
            requires_operator_review=False,
        )
        errs = planner.add_operation(op)
        assert any("requires_operator_review must be True" in e for e in errs)


class TestOperationValidation:
    def test_invalid_operation_type(self):
        op = EditOperation(
            operation_id="e1",
            operation="nonexistent_op",
            anchor="s1",
        )
        errs = op.validate()
        assert any("operation must be one of" in e for e in errs)

    def test_invalid_mode(self):
        op = EditOperation(
            operation_id="e1",
            operation="insert_clip",
            anchor="s1",
            mode="invalid_mode",
        )
        errs = op.validate()
        assert any("mode must be one of" in e for e in errs)

    def test_empty_operation_id(self):
        op = EditOperation(operation_id="", operation="insert_clip", anchor="s1")
        errs = op.validate()
        assert any("operation_id must be non-empty" in e for e in errs)

    def test_default_apply_performed_false(self):
        op = EditOperation(operation_id="e1", operation="insert_clip", anchor="s1")
        assert op.apply_performed is False

    def test_default_requires_operator_review_true(self):
        op = EditOperation(operation_id="e1", operation="insert_clip", anchor="s1")
        assert op.requires_operator_review is True


class TestEditDecisionListSerialization:
    def test_to_json(self):
        planner = EditDecisionPlanner()
        op = EditOperation(operation_id="e1", operation="insert_clip", anchor="s1", apply_performed=False, requires_operator_review=True)
        planner.add_operation(op)
        output = planner.to_json()
        assert '"operation_id": "e1"' in output
        assert '"apply_performed": false' in output
