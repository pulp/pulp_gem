from pulpcore.plugin import PulpPluginAppConfig


class PulpGemPluginAppConfig(PulpPluginAppConfig):
    """Entry point for the gem plugin."""

    name = "pulp_gem.app"
    label = "gem"
    version = "0.2.0"
    python_package_name = "pulp-gem"
