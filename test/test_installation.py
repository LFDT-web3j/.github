import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallationCommandTests(unittest.TestCase):
    def test_failed_download_is_not_executed(self):
        command = (ROOT / "profile/README.md").read_text().split("For Unix:", 1)[1]
        command = command.split("\x60\x60\x60shell script\n", 1)[1].split("\x60\x60\x60", 1)[0]
        for failure in (False, True):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                temp = Path(directory)
                marker = temp / "executed"
                curl = temp / "curl"
                curl.write_text("#!" + sys.executable + "\n" + '''
import os, pathlib, sys
args = sys.argv[1:]
assert args[:5] == ["--disable", "--proto", "=https", "--proto-redir", "=https"], args
for flag in ["--fail", "--show-error", "--silent", "--location"]: assert flag in args
assert "https://get.web3j.io" in args
pathlib.Path(args[args.index("-o")+1]).write_text('printf executed > "$TEST_EXECUTION_MARKER"\\n')
if os.environ["TEST_FAIL_DOWNLOAD"] == "1": sys.exit(18)
''')
                curl.chmod(0o755)
                user_home = temp / "user-home"
                (user_home / ".web3j").mkdir(parents=True)
                (user_home / ".web3j/source.sh").write_text(":\n")
                env = dict(os.environ, PATH=str(temp) + ":/usr/bin:/bin", HOME=str(user_home),
                           TMPDIR=str(temp), TEST_EXECUTION_MARKER=str(marker),
                           TEST_FAIL_DOWNLOAD="1" if failure else "0")
                result = subprocess.run(["bash", "-c", command], env=env, cwd=temp,
                                        capture_output=True, text=True, timeout=10)
                if failure:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(marker.exists())
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(marker.read_text(), "executed")


if __name__ == "__main__":
    unittest.main()

