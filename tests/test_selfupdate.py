"""Update decision and install tests (no network, no Qt): python3 -m unittest discover tests"""
import hashlib
import os
import pathlib
import tempfile
import unittest

from gt6launcher import selfupdate as su


def rel(tag, prerelease=False, draft=False, assets=True):
    a = []
    if assets:
        a = [{"name": su.ASSET_NAME, "browser_download_url": f"https://x/{tag}/{su.ASSET_NAME}"},
             {"name": su.SUMS_NAME, "browser_download_url": f"https://x/{tag}/{su.SUMS_NAME}"}]
    return {"tag_name": tag, "prerelease": prerelease, "draft": draft, "assets": a,
            "html_url": f"https://github.com/r/releases/tag/{tag}"}


class Decision(unittest.TestCase):
    def test_older_same_newer(self):
        self.assertIsNone(su.newer_release("1.0.0", [rel("v0.9.0")]))
        self.assertIsNone(su.newer_release("1.0.0", [rel("v1.0.0")]))
        r = su.newer_release("1.0.0", [rel("v0.9.0"), rel("v1.0.1"), rel("v1.0.0")])
        self.assertEqual(r["tag"], "v1.0.1")
        self.assertTrue(r["appimage_url"].endswith(su.ASSET_NAME))
        self.assertTrue(r["sums_url"].endswith(su.SUMS_NAME))

    def test_test_build_on_top_of_release(self):
        r = su.newer_release("1.0.0", [rel("v1.0.0"), rel("v1.0.1-beta1", prerelease=True)])
        self.assertEqual(r["tag"], "v1.0.1-beta1")
        self.assertEqual(r["version"], "v1.0.1 Test 1")
        # the final release replaces the test build
        r = su.newer_release("1.0.1-beta1", [rel("v1.0.1-beta1", True), rel("v1.0.1")])
        self.assertEqual(r["tag"], "v1.0.1")
        self.assertIsNone(su.newer_release("1.0.1", [rel("v1.0.1-beta2", True)]))

    def test_ignores_drafts_and_junk(self):
        self.assertIsNone(su.newer_release("1.0.0", [rel("v9.0.0", draft=True), rel("nightly")]))

    def test_display(self):
        self.assertEqual(su.display_version("1.0.0"), "v1.0.0")
        self.assertEqual(su.display_version("1.2-test3"), "v1.2.0 Test 3")

    def test_sums(self):
        h = "a" * 64
        self.assertEqual(su.parse_sums(f"{h}  {su.ASSET_NAME}\n", su.ASSET_NAME), h)
        self.assertEqual(su.parse_sums(f"{h} *{su.ASSET_NAME}\n", su.ASSET_NAME), h)
        self.assertIsNone(su.parse_sums(f"{h}  other\n", su.ASSET_NAME))


class Install(unittest.TestCase):
    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp())
        self.target = self.d / "LakuenTurismoRecomp-x86_64.AppImage"
        self.target.write_bytes(b"old")
        os.chmod(self.target, 0o755)
        self.new = self.d / "srv.AppImage"
        self.new.write_bytes(b"new appimage" * 1000)

    def _rel(self, digest):
        sums = self.d / "SHA256SUMS.txt"
        sums.write_text(f"{digest}  {su.ASSET_NAME}\n")
        return {"tag": "v1.0.1", "appimage_url": self.new.as_uri(), "sums_url": sums.as_uri()}

    def test_good(self):
        digest = hashlib.sha256(self.new.read_bytes()).hexdigest()
        seen = []
        out = su.install(self._rel(digest), lambda d, t: seen.append(d), target=str(self.target))
        self.assertEqual(pathlib.Path(out).read_bytes(), self.new.read_bytes())
        self.assertTrue(os.access(out, os.X_OK))
        self.assertTrue(seen)
        self.assertFalse(any(p.name.endswith(".update-part") for p in self.d.iterdir()))

    def test_bad_checksum_keeps_old(self):
        with self.assertRaises(su.UpdateError):
            su.install(self._rel("0" * 64), target=str(self.target))
        self.assertEqual(self.target.read_bytes(), b"old")
        self.assertFalse(any(p.name.endswith(".update-part") for p in self.d.iterdir()))


if __name__ == "__main__":
    unittest.main()
