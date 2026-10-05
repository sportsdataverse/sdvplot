"""The test harness's own workarounds (tests/conftest.py)."""

import os
import threading

import pytest


def test_a_pipe_reader_kaleido_starts_cannot_keep_the_run_alive():
    logistro = pytest.importorskip("logistro")
    w, _ = logistro.getPipeLogger("sdvplot_harness")
    reader = next(t for t in threading.enumerate() if t.name == "sdvplot_harnessThread")
    try:
        assert reader.daemon
    finally:
        os.close(w)
        reader.join(5)
