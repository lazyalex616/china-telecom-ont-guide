"""Offline cases for maintainers to run explicitly; never contacts an ONT."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SafeHelperCases(unittest.TestCase):
    def test_ipv4_rejects_ambiguous_addresses(self):
        clock = load("clock_ipv4", "ont-clock.py")
        for value in ("192.168.01.1", "127.0.0.1", "203.0.113.1", "http://192.168.1.1", "192.168.1.256"):
            with self.assertRaises(RuntimeError):
                clock.private_ipv4(value)
        self.assertEqual(clock.private_ipv4("192.168.1.1"), "192.168.1.1")

    def test_http_date_does_not_use_local_timezone(self):
        clock = load("clock_utc", "ont-clock.py")
        reply = type("Reply", (), {"returncode": 0, "stdout": b"HTTP/1.1 200 OK\r\nDate: Thu, 01 Jan 1970 00:00:00 GMT\r\n"})()
        clock.HOST = "192.168.1.1"
        with patch.object(clock.subprocess, "run", return_value=reply), patch.object(clock.time, "mktime", side_effect=AssertionError("must not depend on local DST")):
            self.assertEqual(clock.http_clock(), 0)

    def test_port_timeout_is_not_reported_closed(self):
        clock = load("clock_port", "ont-clock.py")
        clock.HOST = "192.168.1.1"
        with patch.object(clock.socket, "socket") as socket:
            socket.return_value.__enter__.return_value.connect.side_effect = TimeoutError()
            self.assertEqual(clock.service_state(), "unknown")
            socket.return_value.__enter__.return_value.connect.side_effect = ConnectionRefusedError()
            self.assertEqual(clock.service_state(), "closed")

    def test_config_check_has_no_network_or_credential_output(self):
        clock = load("clock_config", "ont-clock.py")
        config = ROOT / "examples" / "clock-zte.example.json"
        with patch.object(clock.sys, "argv", ["ont-clock.py", str(config), "--check-config"]), patch.object(clock.os, "name", "nt"), patch.object(clock.socket, "socket", side_effect=AssertionError("offline only")), patch("builtins.print") as output:
            clock.main()
        lines = "\n".join(str(call) for call in output.call_args_list)
        self.assertNotIn("REPLACE_WITH_PASSWORD_FROM_TECHNICIAN", lines)

    def test_installer_refuses_existing_destination(self):
        installer = load("skill_install", "install-skill.py")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            target, count = installer.plan(parent)
            self.assertGreater(count, 0)
            self.assertFalse(target.exists())
            target.mkdir()
            with self.assertRaises(ValueError):
                installer.plan(parent)


if __name__ == "__main__":
    unittest.main()
