"""Cycle 4 tests: brain HTTP service (ephemeral port, no fixed deps)."""
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))
from brain.server import Handler, ThreadingHTTPServer


def _free_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _call(base, method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.load(resp)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = _free_server()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_health(self):
        code, body = _call(self.base, "GET", "/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "ok")

    def test_event_drives_commands(self):
        code, body = _call(self.base, "POST", "/event", {"event": "user_started_speaking"})
        self.assertEqual(body["behavior_state"], "LISTENING")
        code, cmds = _call(self.base, "GET", "/commands?since=0")
        self.assertTrue(any(c["type"] == "avatar.state" for c in cmds["commands"]))

    def test_intent_allow_and_deny(self):
        _, ok_body = _call(self.base, "POST", "/intent",
                           {"intent": "workspace.next", "parameters": {}})
        self.assertTrue(ok_body["allowed"])
        _, deny = _call(self.base, "POST", "/intent",
                        {"intent": "shell.exec", "parameters": {}})
        self.assertFalse(deny["allowed"])

    def test_unknown_endpoint_404(self):
        try:
            _call(self.base, "GET", "/nope")
            self.fail("expected HTTPError")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)

    def test_bad_since_400(self):
        try:
            _call(self.base, "GET", "/commands?since=abc")
            self.fail("expected HTTPError")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 400)

    def test_invalid_json_400(self):
        req = urllib.request.Request(self.base + "/event", data=b"{nope",
                                     method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("expected HTTPError")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 400)

    def test_look_at_command_queued(self):
        _call(self.base, "POST", "/event", {"event": "user_started_speaking"})
        _, cmds = _call(self.base, "GET", "/commands?since=0")
        self.assertTrue(any(c["type"] == "avatar.look_at" for c in cmds["commands"]))

    def test_bind_restricted(self):
        from brain.server import run
        with self.assertRaises(ValueError):
            run("0.0.0.0", 18771)


if __name__ == "__main__":
    unittest.main()
