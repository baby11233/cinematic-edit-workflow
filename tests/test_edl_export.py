import argparse
import sys
import unittest
import xml.dom.minidom
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from edl_export import ExportError, build_cmx3600, build_fcpxml, file_uri, load_clips, parse_fps  # noqa: E402

EDL = {
    "version": 2,
    "timeline": {"frame_rate": 25, "width": 1920, "height": 1080},
    "sources": {"SRC0001": "E:/footage/a.mp4", "SRC0002": r"C:/Users/x/b.mp4"},
    "ranges": [
        {"id": "a", "source": "SRC0001", "start": 1.0, "end": 3.0},
        {"id": "b", "source": "SRC0002", "start": 0.0, "end": 1.0, "record_in_seconds": 1.0,
         "video_track": "V2", "transform": "hflip"},
        {"id": "c", "source": "SRC0001", "start": 5.0, "end": 6.0},
    ],
}


def args(**kw):
    base = dict(width=None, height=None, path_map=[], name=None)
    base.update(kw)
    return argparse.Namespace(**base)


class EdlExportTests(unittest.TestCase):
    def test_fps_parsing(self):
        self.assertEqual(parse_fps("24000/1001"), Fraction(24000, 1001))
        self.assertEqual(parse_fps(23.976), Fraction(24000, 1001))
        self.assertEqual(parse_fps(25), Fraction(25))

    def test_tracks_are_independent(self):
        frame = 1 / parse_fps(25)
        clips = load_clips(EDL, frame)
        self.assertEqual([c.rec_in for c in clips], [0, 25, 50])  # V2 overlay does not push V1
        self.assertEqual(clips[1].track, "V2")

    def test_overlap_on_one_track_is_rejected(self):
        bad = {"sources": {"S": "/a.mp4"}, "ranges": [
            {"source": "S", "start": 0, "end": 2}, {"source": "S", "start": 0, "end": 1, "record_in_seconds": 1}]}
        with self.assertRaises(ExportError):
            load_clips(bad, 1 / parse_fps(25))

    def test_fcpxml_is_well_formed_with_lane_and_remap(self):
        frame = 1 / parse_fps(25)
        text = build_fcpxml(EDL, load_clips(EDL, frame), frame, args(path_map=["E:/footage=/Volumes/SSD/footage"]), None)
        xml.dom.minidom.parseString(text)
        self.assertIn('src="file:///Volumes/SSD/footage/a.mp4"', text)
        self.assertIn('src="file:///C:/Users/x/b.mp4"', text)
        self.assertIn('lane="1"', text)
        self.assertIn("hflip", text)

    def test_cmx3600_v1_only(self):
        frame = 1 / parse_fps(25)
        text = build_cmx3600(EDL, load_clips(EDL, frame), frame, args())
        self.assertIn("001  SRC0001", text)
        self.assertNotIn("SRC0002", text)

    def test_relative_source_path_rejected(self):
        with self.assertRaises(ExportError):
            file_uri("footage/a.mp4", [])


if __name__ == "__main__":
    unittest.main()
