from pulpcore.plugin import PulpPluginAppConfig


class PulpGemPluginAppConfig(PulpPluginAppConfig):
    """Entry point for the gem plugin."""

    name = "pulp_gem.app"
    label = "gem"
    version = "0.5.0.dev"
    python_package_name = "pulp-gem"
    domain_compatible = True
