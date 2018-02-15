from pulpcore.plugin import PulpPluginAppConfig


class PulpGemPluginAppConfig(PulpPluginAppConfig):
    name = 'pulp_gem.app'
    label = 'pulp_gem'
