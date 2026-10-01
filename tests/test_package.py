import sdvplot
from sdvplot import _errors


def test_version_is_a_string():
    assert isinstance(sdvplot.__version__, str) and sdvplot.__version__


def test_error_types_subclass_the_builtin_they_extend():
    assert issubclass(_errors.SdvplotWarning, UserWarning)
    assert issubclass(_errors.UnresolvedTeamError, ValueError)
    assert issubclass(_errors.OfflineError, RuntimeError)
    assert issubclass(_errors.OptionalDependencyError, ImportError)
    assert issubclass(_errors.UnsupportedTargetError, TypeError)
