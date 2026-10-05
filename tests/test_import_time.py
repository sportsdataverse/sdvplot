import subprocess
import sys


def test_import_does_not_load_the_heavy_dependencies():
    code = "import sdvplot, sys; print('requests' in sys.modules, 'PIL' in sys.modules, 'polars' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout
    assert out.split() == ["False", "False", "False"]


def test_the_lazy_dependencies_load_when_used():
    code = "import sdvplot, sys; sdvplot.teams('nfl'); print('polars' in sys.modules)"
    assert (
        subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.strip()
        == "True"
    )
