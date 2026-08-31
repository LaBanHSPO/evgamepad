"""The reactor guard, exercised in subprocesses because installing one is a global, once-only act."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

GATEWAY = Path(__file__).resolve().parents[1]


def run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code], cwd=GATEWAY, capture_output=True, text=True, timeout=60
    )


def test_install_gives_us_the_asyncio_reactor() -> None:
    result = run(
        "from broker.reactor_setup import install;"
        "from twisted.internet.asyncioreactor import AsyncioSelectorReactor;"
        "r = install();"
        "assert isinstance(r, AsyncioSelectorReactor), type(r);"
        "print('ok')"
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_install_is_idempotent() -> None:
    result = run(
        "from broker.reactor_setup import install;"
        "a = install(); b = install();"
        "assert a is b;"
        "print('ok')"
    )
    assert result.returncode == 0, result.stderr


def test_a_foreign_reactor_boot_fails_with_a_named_error() -> None:
    """The failure mode this guards against is silent, so the guard must be loud."""
    result = run(
        "import twisted.internet.selectreactor as s, twisted.internet.main as m;"
        "m.installReactor(s.SelectReactor());"
        "import sys;"
        "from broker.reactor_setup import install, ReactorMismatch;"
        "\ntry:\n"
        "    install()\n"
        "except ReactorMismatch as exc:\n"
        "    print('boot-fail:', exc, file=sys.stderr); sys.exit(2)\n"
        "sys.exit(0)"
    )
    assert result.returncode == 2, f"expected a boot-fail, got {result.returncode}: {result.stdout}"
    assert "SelectReactor" in result.stderr
    assert "asyncioreactor" in result.stderr


def test_verify_installed_refuses_a_bare_process() -> None:
    result = run(
        "import sys;"
        "from broker.reactor_setup import verify_installed, ReactorMismatch;"
        "\ntry:\n"
        "    verify_installed()\n"
        "except ReactorMismatch as exc:\n"
        "    print(exc, file=sys.stderr); sys.exit(2)\n"
        "sys.exit(0)"
    )
    assert result.returncode == 2
    assert "no reactor installed" in result.stderr


def test_importing_the_vendor_client_first_lands_on_the_wrong_reactor() -> None:
    """The hazard the conftest guard exists for, pinned so it cannot regress quietly.

    `ctrader_open_api` reaches `twisted.internet.reactor` at import time. An import sorter that
    puts it above `broker.ctrader` is enough to change which reactor the process runs on — and
    the symptom of getting that wrong is not a crash, it is a socket that merely seems slow.
    """
    result = run(
        "import sys;"
        "import ctrader_open_api;"          # installs twisted's default reactor
        "\ntry:\n"
        "    import broker.ctrader\n"
        "except Exception as exc:\n"
        "    print(type(exc).__name__, exc, file=sys.stderr); sys.exit(2)\n"
        "sys.exit(0)"
    )
    assert result.returncode == 2, "importing the vendor client first must be caught, not tolerated"
    assert "ReactorMismatch" in result.stderr


def test_importing_the_broker_first_is_safe() -> None:
    """The supported order: ours goes in, then the vendor client rides on it."""
    result = run(
        "import broker.ctrader, sys;"
        "import ctrader_open_api;"
        "from twisted.internet.asyncioreactor import AsyncioSelectorReactor;"
        "assert isinstance(sys.modules['twisted.internet.reactor'], AsyncioSelectorReactor);"
        "print('ok')"
    )
    assert result.returncode == 0, result.stderr
