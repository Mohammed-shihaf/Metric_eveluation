"""Tests for branch pipeline helpers."""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

from lib.branch_pipeline import (
    _deadline_passed,
    apply_current_scores,
    build_regeneration_strength_map,
    ensure_local_branches,
    generate_branches,
    next_regen_strength,
    push_branches,
    snapshot_previous_scores,
    sync_gen_rows_strength_from_work,
    update_regenerated_strength,
)
from lib.lang_generators.base import scaled_n_functions, scaled_test_count


def _iter_branches_stub(techniques, metrics, types, version, registry=None):
    for bt in types or []:
        yield "DF", "MET", bt, "DF_MET_%s_2.6" % bt


class NextRegenStrengthTests(unittest.TestCase):
    def test_new_branch_is_zero(self):
        self.assertEqual(next_regen_strength(0, 0, 0, exists=False), 0)

    def test_existing_increments_max(self):
        self.assertEqual(next_regen_strength(4, 5, 3, exists=True), 6)
        self.assertEqual(next_regen_strength(0, 0, 6, exists=True), 7)

    def test_unknown_existing_defaults_to_one(self):
        self.assertEqual(next_regen_strength(0, 0, 0, exists=True), 1)


class StrengthMapParityTests(unittest.TestCase):
    def test_gen_rows_session_included_in_map(self):
        with tempfile.TemporaryDirectory() as work_root:
            branch = "DF_MET_Bug_2.6"
            branch_dir = os.path.join(work_root, branch)
            os.makedirs(branch_dir)
            with open(os.path.join(branch_dir, ".gen_meta.json"), "w", encoding="utf-8") as fh:
                json.dump({"strength": 4, "loc": 3000}, fh)

            gen_rows = [{"branch_name": branch, "strength": 6, "generated": True, "dir": branch_dir}]
            strength_map = build_regeneration_strength_map(
                work_root,
                [branch],
                gen_rows=gen_rows,
            )
            self.assertEqual(strength_map[branch], 7)

    def test_display_and_generate_share_helper(self):
        local = 4
        remote = 5
        session = 3
        expected = next_regen_strength(local, remote, session, exists=True)
        self.assertEqual(expected, 6)


class ScaledFunctionsMonotonicTests(unittest.TestCase):
    def test_each_strength_step_adds_functions(self):
        base = 72
        prev = scaled_n_functions(base, 1)
        for strength in range(2, 8):
            current = scaled_n_functions(base, strength)
            self.assertGreater(current, prev)
            prev = current


class ScaledTestCountTests(unittest.TestCase):
    def test_thoroughness_ratio_increases_with_strength(self):
        n_fn = 88
        prev_ratio = 0.0
        for strength in range(4, 10):
            count = scaled_test_count(n_fn, "CC", strength)
            ratio = float(count) / float(n_fn)
            self.assertGreater(ratio, prev_ratio)
            prev_ratio = ratio

    def test_reaches_full_coverage_at_high_strength(self):
        n_fn = 88
        count = scaled_test_count(n_fn, "TCC", 9)
        self.assertEqual(count, n_fn)

    def test_bug_always_one_test(self):
        self.assertEqual(scaled_test_count(88, "Bug", 6), 1)


class SyncGenRowsTests(unittest.TestCase):
    def test_sync_updates_strength_from_disk(self):
        with tempfile.TemporaryDirectory() as work_root:
            branch = "DF_MET_Bug_2.6"
            branch_dir = os.path.join(work_root, branch)
            os.makedirs(branch_dir)
            with open(os.path.join(branch_dir, ".gen_meta.json"), "w", encoding="utf-8") as fh:
                json.dump({"strength": 9, "loc": 4000}, fh)

            rows = [{"branch_name": branch, "strength": 4, "dir": branch_dir}]
            sync_gen_rows_strength_from_work(rows, work_root)
            self.assertEqual(rows[0]["strength"], 9)
            self.assertEqual(rows[0]["loc"], 4000)


class EnsureLocalBranchesTests(unittest.TestCase):
    def test_skips_existing_local_and_fetches_missing_remote(self):
        with tempfile.TemporaryDirectory() as work_root:
            local_branch = "DF_MET_Bug_2.6"
            remote_branch = "DF_MET_CC_2.6"
            local_dir = os.path.join(work_root, local_branch)
            os.makedirs(os.path.join(local_dir, "df"))
            with open(os.path.join(local_dir, "df", "config.py"), "w") as fh:
                fh.write("# config")
            with open(os.path.join(local_dir, ".gen_meta.json"), "w", encoding="utf-8") as fh:
                fh.write('{"strength": 1, "loc": 100}')

            push_rows = [
                {"branch": local_branch, "on_github": "yes"},
                {"branch": remote_branch, "on_github": "yes"},
            ]
            github_config = {"token": "tok", "repo_slug": "owner/repo"}

            def fake_fetch(token, repo_slug, ref, dest_dir):
                self.assertEqual(ref, remote_branch)
                os.makedirs(dest_dir, exist_ok=True)
                with open(os.path.join(dest_dir, ".gen_meta.json"), "w", encoding="utf-8") as fh:
                    fh.write('{"strength": 2, "loc": 200}')

            with patch("lib.branch_pipeline.iter_branches", side_effect=_iter_branches_stub):
                with patch("lib.branch_pipeline.fetch_branch_source", side_effect=fake_fetch):
                    gen_rows, materialized, errors = ensure_local_branches(
                        work_root,
                        github_config,
                        "DF",
                        "MET",
                        ["Bug", "CC"],
                        "2.6",
                        push_rows=push_rows,
                    )

            self.assertEqual(materialized, [remote_branch])
            self.assertEqual(errors, [])
            self.assertEqual(len(gen_rows), 2)
            names = {r["branch_name"] for r in gen_rows}
            self.assertEqual(names, {local_branch, remote_branch})

    def test_no_fetch_when_not_on_github(self):
        with tempfile.TemporaryDirectory() as work_root:
            with patch("lib.branch_pipeline.iter_branches", side_effect=_iter_branches_stub):
                with patch("lib.branch_pipeline.fetch_branch_source") as mock_fetch:
                    gen_rows, materialized, errors = ensure_local_branches(
                        work_root,
                        {"token": "tok", "repo_slug": "owner/repo"},
                        "DF",
                        "MET",
                        ["Bug"],
                        "2.6",
                        push_rows=[{"branch": "DF_MET_Bug_2.6", "on_github": "no"}],
                    )
            mock_fetch.assert_not_called()
            self.assertEqual(materialized, [])
            self.assertEqual(gen_rows, [])


class PipelineStepLabelTests(unittest.TestCase):
    def test_step_transitions(self):
        from ui.app import _pipeline_step_label

        self.assertEqual(_pipeline_step_label(False, False, False, False)[0], 1)
        self.assertEqual(_pipeline_step_label(True, False, False, False)[0], 2)
        self.assertEqual(_pipeline_step_label(True, True, True, False)[0], 3)
        self.assertEqual(_pipeline_step_label(True, True, True, True)[0], 4)


class GenerateDeadlineTests(unittest.TestCase):
    def test_stops_at_deadline_with_remaining(self):
        planned = [
            ("SA", "MET", "Bug", "B1"),
            ("SA", "MET", "CC", "B2"),
            ("SA", "MET", "TCC", "B3"),
        ]

        with tempfile.TemporaryDirectory() as work_root:
            call_count = {"n": 0}

            def fake_deadline(deadline):
                call_count["n"] += 1
                return call_count["n"] > 1

            with patch("lib.branch_pipeline.iter_branches", return_value=planned):
                with patch("lib.branch_pipeline._deadline_passed", side_effect=fake_deadline):
                    with patch("lib.branch_pipeline.write_branch", return_value=("B1", 100)):
                        with patch(
                            "lib.branch_pipeline.verify_generated_branch",
                            return_value={"ok": True, "loc": 100, "messages": []},
                        ):
                            with patch("lib.branch_pipeline.read_gen_meta", return_value={"strength": 1, "loc": 100}):
                                result = generate_branches(
                                    "SA", "MET", ["Bug", "CC", "TCC"], "2.6", "python", work_root,
                                    deadline=time.time() + 60,
                                )

        self.assertEqual(result["stop_cause"], "time_budget")
        self.assertEqual(result["completed"], ["B1"])
        self.assertEqual(result["remaining"], ["B2", "B3"])
        self.assertFalse(result["success"])


class PushContinueTests(unittest.TestCase):
    def test_continues_after_branch_failure(self):
        rows = [
            {
                "branch_name": "B1", "technique_code": "SA", "metric_code": "MET",
                "branch_type": "Bug", "dir": "/tmp/b1", "overall": "PASS",
            },
            {
                "branch_name": "B2", "technique_code": "SA", "metric_code": "MET",
                "branch_type": "CC", "dir": "/tmp/b2", "overall": "PASS",
            },
            {
                "branch_name": "B3", "technique_code": "SA", "metric_code": "MET",
                "branch_type": "TCC", "dir": "/tmp/b3", "overall": "PASS",
            },
        ]
        github_config = {"token": "tok", "repo_slug": "owner/repo", "default_branch": "main", "login": "user"}

        def fake_push(*args, **kwargs):
            bname = args[2]
            if bname == "B2":
                return None, "write denied", "oauth"
            return "abc123", None, "oauth"

        with patch("lib.branch_pipeline.check_app_repo_access", return_value=(True, False, "ok")):
            with patch("lib.branch_pipeline.os.path.isdir", return_value=True):
                with patch("lib.branch_pipeline.branch_materialized", return_value=True):
                    with patch("lib.branch_pipeline.read_gen_meta", return_value={"strength": 1, "version": "2.6", "language": "python"}):
                        with patch("lib.branch_pipeline.generate_branch_files", return_value={}):
                            with patch("lib.branch_pipeline.push_branch_to_github", side_effect=fake_push):
                                result = push_branches(rows, github_config)

        self.assertFalse(result["success"])
        self.assertEqual(sorted(result["completed"]), ["B1", "B3"])
        self.assertEqual(result["failed"], ["B2"])
        self.assertEqual(result["remaining"], ["B2"])
        self.assertEqual(result["stop_cause"], "errors")
        self.assertEqual(len(result["rows"]), 3)


class GenerateAutoFixTests(unittest.TestCase):
    def test_verify_failure_is_auto_fixed(self):
        planned = [("SA", "MET", "Bug", "B1")]
        verify_results = [
            {"ok": False, "loc": 100, "messages": ["pytest failed"]},
            {"ok": True, "loc": 120, "messages": ["pytest OK"]},
        ]

        with tempfile.TemporaryDirectory() as work_root:
            with patch("lib.branch_pipeline.iter_branches", return_value=planned):
                with patch("lib.branch_pipeline.write_branch", return_value=("B1", 100)):
                    with patch(
                        "lib.branch_pipeline.verify_generated_branch",
                        side_effect=verify_results,
                    ):
                        with patch(
                            "lib.branch_pipeline.read_gen_meta",
                            return_value={"strength": 1, "loc": 120},
                        ):
                            with patch("lib.branch_pipeline._fix_branch", return_value="regenerated") as fix:
                                result = generate_branches(
                                    "SA", "MET", ["Bug"], "2.6", "python", work_root,
                                    max_fix_attempts=3,
                                    auto_install=False,
                                )

        self.assertTrue(result["success"])
        self.assertEqual(result["completed"], ["B1"])
        self.assertEqual(result["remaining"], [])
        self.assertEqual(fix.call_count, 1)

    def test_verify_failure_unfixed_after_attempts(self):
        planned = [("SA", "MET", "Bug", "B1")]

        with tempfile.TemporaryDirectory() as work_root:
            with patch("lib.branch_pipeline.iter_branches", return_value=planned):
                with patch("lib.branch_pipeline.write_branch", return_value=("B1", 100)):
                    with patch(
                        "lib.branch_pipeline.verify_generated_branch",
                        return_value={"ok": False, "loc": 100, "messages": ["pytest failed"]},
                    ):
                        with patch(
                            "lib.branch_pipeline.read_gen_meta",
                            return_value={"strength": 1, "loc": 100},
                        ):
                            with patch("lib.branch_pipeline._fix_branch", return_value="regenerated") as fix:
                                result = generate_branches(
                                    "SA", "MET", ["Bug"], "2.6", "python", work_root,
                                    max_fix_attempts=2,
                                    auto_install=False,
                                )

        self.assertFalse(result["success"])
        self.assertEqual(result["remaining"], ["B1"])
        self.assertEqual(fix.call_count, 2)


class DeadlineHelperTests(unittest.TestCase):
    def test_deadline_passed_none_is_false(self):
        self.assertFalse(_deadline_passed(None))

    def test_deadline_passed_future_is_false(self):
        self.assertFalse(_deadline_passed(time.time() + 60))

    def test_deadline_passed_past_is_true(self):
        self.assertTrue(_deadline_passed(time.time() - 1))


class ScoreHistoryTests(unittest.TestCase):
    def test_snapshot_moves_cur_to_prev_only_for_regenerated(self):
        history = {
            "B1": {"cur_strength": 4, "cur_score": 12.5, "regenerated": True},
            "B2": {"cur_strength": 3, "cur_score": 10.0, "regenerated": False},
        }
        out = snapshot_previous_scores(
            history,
            {"B1"},
            last_strength_by_branch={"B3": 2},
            last_score_by_branch={"B3": 8.0},
        )
        self.assertEqual(out["B1"]["prev_strength"], 4)
        self.assertEqual(out["B1"]["prev_score"], 12.5)
        self.assertIsNone(out["B1"]["cur_strength"])
        self.assertIsNone(out["B1"]["cur_score"])
        self.assertTrue(out["B1"]["regenerated"])
        self.assertEqual(out["B2"]["cur_strength"], 3)
        self.assertEqual(out["B2"]["cur_score"], 10.0)
        self.assertNotIn("B3", out)

    def test_snapshot_falls_back_to_last_maps_when_history_empty(self):
        out = snapshot_previous_scores(
            {},
            {"DF_MET_Bug_2.6"},
            last_strength_by_branch={"DF_MET_Bug_2.6": 5},
            last_score_by_branch={"DF_MET_Bug_2.6": 14.2},
        )
        entry = out["DF_MET_Bug_2.6"]
        self.assertEqual(entry["prev_strength"], 5)
        self.assertEqual(entry["prev_score"], 14.2)
        self.assertTrue(entry["regenerated"])

    def test_update_regenerated_strength_sets_cur_from_gen_rows(self):
        history = {"B1": {"regenerated": True, "prev_strength": 4, "prev_score": 10.0}}
        out = update_regenerated_strength(
            history,
            [{"branch_name": "B1", "strength": 6}, {"branch_name": "B2", "strength": 3}],
        )
        self.assertEqual(out["B1"]["cur_strength"], 6)
        self.assertNotIn("B2", out)

    def test_apply_current_scores_writes_cur_score_and_strength(self):
        history = {"B1": {"regenerated": True, "prev_score": 10.0, "prev_strength": 4}}
        out = apply_current_scores(
            history,
            [{"branch_name": "B1", "strength_score": 13.5, "strength": 6}],
        )
        self.assertEqual(out["B1"]["cur_score"], 13.5)
        self.assertEqual(out["B1"]["cur_strength"], 6)

    def test_round_trip_snapshot_then_validate_shows_improvement(self):
        history = snapshot_previous_scores(
            {},
            {"B1"},
            last_strength_by_branch={"B1": 4},
            last_score_by_branch={"B1": 10.0},
        )
        history = update_regenerated_strength(
            history,
            [{"branch_name": "B1", "strength": 5}],
        )
        history = apply_current_scores(
            history,
            [{"branch_name": "B1", "strength_score": 12.5, "strength": 5}],
        )
        entry = history["B1"]
        self.assertEqual(entry["prev_strength"], 4)
        self.assertEqual(entry["cur_strength"], 5)
        self.assertEqual(entry["prev_score"], 10.0)
        self.assertEqual(entry["cur_score"], 12.5)
        self.assertGreater(entry["cur_score"], entry["prev_score"])


if __name__ == "__main__":
    unittest.main()
