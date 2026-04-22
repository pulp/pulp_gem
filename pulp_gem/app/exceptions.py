from gettext import gettext as _

from pulpcore.plugin.exceptions import PulpException


class RemoteURLRequiredError(PulpException):
    """
    Raised when a sync is attempted without a URL on the remote.
    """

    error_code = "GEM0001"

    def __str__(self):
        return f"[{self.error_code}] " + _("A remote must have a url specified to synchronize.")


class RemoteConnectionError(PulpException):
    """
    Raised when a connection to the remote host fails.
    """

    error_code = "GEM0002"

    def __init__(self, host):
        self.host = host

    def __str__(self):
        return f"[{self.error_code}] " + _("Could not connect to host {host}").format(
            host=self.host
        )


class InvalidGemNameError(PulpException):
    """
    Raised when a gem name does not match the expected format.
    """

    error_code = "GEM0003"

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"[{self.error_code}] " + _("Invalid gem name: {name}").format(name=self.name)


class InvalidRequirementError(PulpException):
    """
    Raised when a gem info file contains an unrecognized requirement key.
    """

    error_code = "GEM0004"

    def __init__(self, stmt):
        self.stmt = stmt

    def __str__(self):
        return f"[{self.error_code}] " + _("Invalid requirement: {stmt}").format(stmt=self.stmt)


class InvalidVersionStringError(PulpException):
    """
    Raised when a gem version string does not match the expected format.
    """

    error_code = "GEM0005"

    def __init__(self, version):
        self.version = version

    def __str__(self):
        return f"[{self.error_code}] " + _("Invalid version string: {version}").format(
            version=self.version
        )


class UnknownRubyClassError(PulpException):
    """
    Raised when YAML parsing encounters an unknown Ruby class.
    """

    error_code = "GEM0006"

    def __init__(self, suffix):
        self.suffix = suffix

    def __str__(self):
        return f"[{self.error_code}] " + _("Unknown ruby class {suffix}.").format(
            suffix=self.suffix
        )
