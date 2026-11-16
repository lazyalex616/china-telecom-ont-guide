"""供维护者显式运行的离线检查，只调用模板地址校验，不启动 SSH。"""

import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "posix", "需要 POSIX sh；不启动设备或服务")
class SSHAddressCases(unittest.TestCase):
    def validate(self, address):
        source = (ROOT / "tools/ont-ssh.init").read_text(encoding="utf-8")
        result = subprocess.run(
            ["sh", "-c", source + "\nLISTEN_ADDRESS=$1\nvalid_address\n", "ont-ssh-template", address],
            capture_output=True, timeout=3,
        )
        return result.returncode == 0

    def test_only_unambiguous_private_ipv4_is_allowed(self):
        for value in ("10.0.0.1", "172.16.0.1", "172.31.255.254", "192.168.1.1"):
            with self.subTest(value=value):
                self.assertTrue(self.validate(value))

    def test_placeholders_public_wildcard_and_malformed_addresses_are_rejected(self):
        for value in (
            "REPLACE_WITH_VERIFIED_ONT_MANAGEMENT_IPV4", "", "0.0.0.0", "::", "127.0.0.1",
            "203.0.113.1", "172.15.0.1", "172.32.0.1", "192.169.1.1", "192.168.01.1",
            "192.168.1.256", "192.168.1", "192.168.1.1.", ".192.168.1.1", "192..168.1.1",
            "192.168.1.1:22", "192.168.example.com", "192.168.1.1;exit 0", "192.168.1.1\n",
            "192.168.1.999999999999999999999999", "192.168.*.1",
        ):
            with self.subTest(value=value):
                self.assertFalse(self.validate(value))


if __name__ == "__main__":
    unittest.main()
