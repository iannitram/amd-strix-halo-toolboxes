"""Locked tests for #15 (workstation/redact.py). One test per Expectation sentence."""

import copy

from workstation.redact import redact


def test_e1_returns_new_object_and_never_changes_input():
    data = {"a": ["/home/alice/x", {"token": "t"}], "b": ("y",)}
    before = copy.deepcopy(data)
    out = redact(data)
    assert data == before
    assert out is not data
    assert out["a"] is not data["a"]


def test_e2_shapes_and_scalars():
    data = {"z": 1, "a": 2.5, "m": True, "n": None, "l": [1, "x"], "t": ("p", 3)}
    out = redact(data)
    assert list(out) == ["z", "a", "m", "n", "l", "t"]
    assert out == {"z": 1, "a": 2.5, "m": True, "n": None, "l": [1, "x"], "t": ["p", 3]}
    assert isinstance(out["t"], list)


def test_e3_secret_keys_any_value_any_depth():
    data = {"API-Key": "abc", "Authorization": {"x": 1}, "hf_token": None,
            "nested": [{"Password": 5, "keep": "v"}]}
    out = redact(data)
    assert out == {"API-Key": "[redacted]", "Authorization": "[redacted]",
                   "hf_token": "[redacted]", "nested": [{"Password": "[redacted]", "keep": "v"}]}


def test_e4_private_keys():
    data = {"Messages": [{"role": "user"}], "system-prompt": "s", "other": "o"}
    assert redact(data) == {"Messages": "[private]", "system-prompt": "[private]", "other": "o"}


def test_e5_home_dirs_replaced_in_order_keys_untouched():
    data = {"/srv/me": "/srv/me/models/a.gguf", "l": ["run /data/me/x and /srv/me"]}
    out = redact(data, home_dirs=("/srv/me", "/data/me"))
    assert out == {"/srv/me": "~/models/a.gguf", "l": ["run ~/x and ~"]}


def test_e6_unix_and_mac_homes():
    cases = {
        "/home/alice/m.gguf": "~/m.gguf",
        "--model=/home/bob/m.gguf": "--model=~/m.gguf",
        "/var/home/carol/x": "~/x",
        "/Users/dave/Library": "~/Library",
        "cmd /home/eve": "cmd ~",
        "'/home/fay/a b'": "'~/a b'",
    }
    for given, expected in cases.items():
        assert redact(given) == expected


def test_e7_windows_homes():
    assert redact("C:\\Users\\Al\\m.gguf") == "~\\m.gguf"
    assert redact("path=d:\\Users\\Bo") == "path=~"


def test_e8_other_paths_kept():
    for s in ("/srv/models/a.gguf", "/opt/home/x", "x/home/y", "/homework/a", "C:\\Data\\Users"):
        assert redact(s) == s
