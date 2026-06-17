"""Shared fixtures for the wizard tests: in-memory keychain, fake runner, mock HTTP."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from types import SimpleNamespace

import httpx
import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError


class MemoryKeyring(KeyringBackend):
    """A throwaway in-memory keyring backend for tests."""

    priority = 1

    def __init__(self) -> None:
        super().__init__()  # type: ignore[no-untyped-call]
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        try:
            del self.store[(service, username)]
        except KeyError as exc:
            raise PasswordDeleteError(str(exc)) from exc


@pytest.fixture
def memory_keyring() -> Iterator[MemoryKeyring]:
    previous = keyring.get_keyring()
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@dataclass
class FakeRunner:
    """Records subprocess invocations and returns a canned CompletedProcess."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    calls: list[SimpleNamespace] = field(default_factory=list)

    def __call__(
        self,
        args: Sequence[str],
        *,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
        input: str | None = None,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append(
            SimpleNamespace(args=list(args), cwd=cwd, env=env, input=input)
        )
        return subprocess.CompletedProcess(
            list(args), self.returncode, self.stdout, self.stderr
        )


def mock_client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    """An httpx.Client whose every request is answered by ``handler``."""
    return httpx.Client(transport=httpx.MockTransport(handler))
