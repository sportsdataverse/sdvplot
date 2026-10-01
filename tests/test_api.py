import sdvplot

PUBLIC = {
    "resolve",
    "suggest",
    "teams",
    "palette",
    "team_colors",
    "logo_url",
    "logo_image",
    "marks",
    "headshot_url",
    "versions",
    "clear_cache",
    "add_logos",
    "add_wordmarks",
    "add_headshots",
    "axis_logos",
    "SdvplotWarning",
    "UnresolvedTeamError",
    "OfflineError",
    "OptionalDependencyError",
    "UnsupportedTargetError",
    "__version__",
}


def test_the_public_api_is_exactly_the_spec():
    assert set(sdvplot.__all__) == PUBLIC
    for name in PUBLIC:
        assert hasattr(sdvplot, name), name


def test_versions_reports_package_index_and_manifest(cache):
    v = sdvplot.versions()
    assert v["sdvplot"] == sdvplot.__version__ and v["index"] == "fixture" and v["manifest_last_modified"] is None
