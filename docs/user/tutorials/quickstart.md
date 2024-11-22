# User Setup

### Server Installation

Follow the [Installation Quickstart](site:pulp-oci-images/docs/admin/tutorials/quickstart) instructions to get started with Pulp.
Further details are discussed in the [pulpcore documentation](https://docs.pulpproject.org/pulpcore/installation/instructions.html).

### CLI Installation

All workflow examples use the [Pulp CLI](https://docs.pulpproject.org/pulp_cli/).
Install and setup from PyPI:

=== "pip"

    ```bash
    pip install pulp-cli[pygments] pulp-cli-gem

    pulp config create -e
    pulp status  # Check that CLI can talk to Pulp
    ```

=== "pipx"

    ```bash
    pipx install pulp-cli[pygments]
    pipx inject pulp-cli pulp-cli-gem

    pulp config create -e
    pulp status  # Check that CLI can talk to Pulp
    ```

If you configured the `admin` user with a different password, adjust the configuration accordingly.
If you prefer to specify the `username` and `password` with each request,
please see [`Pulp CLI` documentation](https://docs.pulpproject.org/pulp_cli/configuration/) on how to do that.
