import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jianying_patch_compiler import CompileError, compile_patch  # noqa: E402


class JianyingPatchCompilerTests(unittest.TestCase):
    def test_compiles_seconds_and_explicit_overlay_position(self):
        edl = {
            "version": 2,
            "ranges": [
                {"id": "a", "source": "SRC1", "start": 1.25, "end": 2.5, "role": "master"},
                {
                    "id": "b",
                    "source": "SRC2",
                    "source_in_us": 500000,
                    "source_out_us": 1250000,
                    "record_in_us": 250000,
                    "video_track": "V2",
                    "transform": "reframe",
                },
            ],
        }
        material_map = {"materials": {"SRC1": "m1", "SRC2": {"material_id": "m2"}}}
        patch = compile_patch(edl, material_map, "p1", "local://draft-1", "run-1", 4)

        self.assertEqual(patch["baseRevision"], 4)
        self.assertEqual([op["op"] for op in patch["operations"][:2]], ["add_track", "add_track"])
        first = patch["operations"][2]
        second = patch["operations"][3]
        self.assertEqual((first["inUs"], first["outUs"], first["durationUs"]), (1250000, 2500000, 1250000))
        self.assertEqual(second["startUs"], 250000)
        self.assertEqual(second["trackId"], "V2")
        self.assertEqual(second["metadata"]["transformIntent"], "reframe")

    def test_rejects_missing_material_id(self):
        edl = {"ranges": [{"source": "SRC1", "start": 0, "end": 1}]}
        with self.assertRaises(CompileError):
            compile_patch(edl, {"materials": {}}, "p1", "local://draft-1", "run-1", 0)

    def test_rejects_invalid_range(self):
        edl = {"ranges": [{"source": "SRC1", "start": 2, "end": 1}]}
        with self.assertRaises(CompileError):
            compile_patch(edl, {"materials": {"SRC1": "m1"}}, "p1", "local://draft-1", "run-1", 0)


if __name__ == "__main__":
    unittest.main()
