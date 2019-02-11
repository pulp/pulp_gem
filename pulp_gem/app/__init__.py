from pulpcore.plugin import PulpPluginAppConfig


class PulpGemPluginAppConfig(PulpPluginAppConfig):
    """
    Entry point for pulp_gem plugin.
    """

    name = 'pulp_gem.app'
    label = 'gem'
