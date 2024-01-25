# User Setup

All workflow examples use the Pulp CLI. Install and setup from PyPI:

```bash
pip install pulp-cli[pygments] pulp-cli-gem
pulp config create -e
pulp status # Check that CLI can talk to Pulp
```

If you configured the `admin` user with a different password, adjust the configuration
accordingly. If you prefer to specify the username and password with each request, please see
`Pulp CLI` documentation on how to do that.

### Install

=== "Containerized Installation"

    Follow the [Pulp in One Container](https://pulpproject.org/pulp-in-one-container/) instructions to get started with Pulp by
    leveraging OCI images. Further details are discussed in the [pulpcore documentation](https://docs.pulpproject.org/pulpcore/installation/instructions.html).

=== "From Source"

    ```bash
    sudo -u pulp -i
    source ~/pulp/bin/activate
    cd pulp_gem
    pip install -e .
    django-admin runserver 24817
    ```

### Make and Run Migrations

```bash
pulp-manager makemigrations pulp_gem
pulp-manager migrate pulp_gem
```

### Run Services

```bash
pulp-manager runserver
gunicorn pulpcore.content:server --bind 'localhost:24816' --worker-class 'aiohttp.GunicornWebWorker' -w 2
sudo systemctl restart pulpcore-resource-manager
sudo systemctl restart pulpcore-worker@1
sudo systemctl restart pulpcore-worker@2
```
