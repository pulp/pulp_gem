# Cache rubygems.org 

In this guide you will configure Pulp to act as a pull-through cache of `rubygems.org`.
After this, the first time a gem will be requested from Pulp, it will be downloaded from rubygems.org.
The gem will be simultaneously streamed to the client.
The gem will then be saved in Pulp.
On subsequent requests for the same gem, Pulp will return the saved copy.

## 1. Create a Gem Remote

Create a remote named `rubygems.org`.
Set the URL to `https://index.rubygems.org/`.

=== "run"
    ```bash
    pulp gem remote create --name rubygems.org --url https://index.rubygems.org/
    ```

=== "output"
    ```json
    {
        "pulp_href": "/pulp/api/v3/remotes/gem/gem/0188e505-157c-7565-8474-e607e0dbc4a0/",
        "pulp_created": "2023-06-22T21:31:35.676442Z",
        "name": "rubygems.org",
        "url": "https://index.rubygems.org",
        "ca_cert": null,
        "client_cert": null,
        "tls_validation": true,
        "proxy_url": null,
        "pulp_labels": {},
        "pulp_last_updated": "2023-06-22T21:31:35.676454Z",
        "download_concurrency": null,
        "max_retries": null,
        "policy": "immediate",
        "total_timeout": null,
        "connect_timeout": null,
        "sock_connect_timeout": null,
        "sock_read_timeout": null,
        "headers": null,
        "rate_limit": null,
        "hidden_fields": [...],
        "prereleases": false,
        "includes": null,
        "excludes": null
    }
    ```

## 2. Create a Gem Distribution

Create a Gem Distribution named `rubygems.org.cache` and associate the `rubygems.org` remote with it.

=== "run"
    ```bash
    pulp gem distribution create --name rubygems.org.cache \
      --base-path rubygems --remote rubygems.org
    ```
=== "output"
    ```json
    {
      "pulp_href": "/pulp/api/v3/distributions/gem/gem/0188e513-594c-7c44-aaff-beed0f97363e/",
      "pulp_created": "2023-06-22T21:47:10.540670Z",
      "base_path": "rubygems",
      "base_url": "http://localhost:5001/pulp/content/rubygems/",
      "content_guard": null,
      "hidden": false,
      "pulp_labels": {},
      "name": "rubygems.org.cache",
      "repository": null,
      "publication": null,
      "remote": "/pulp/api/v3/remotes/gem/gem/0188e505-157c-7565-8474-e607e0dbc4a0/"
    }
    ```

## 3. Install a gem from Pulp

Run the `gem install` command.
Use the Gem Distribution's `base_url` as the value for the `--source` parameter.

=== "run"
    ```bash
    gem install --source http://localhost:5001/pulp/content/rubygems/ \
      --clear-sources pulpcore_client
    ```
=== "output"
    ```bash
    Building native extensions. This could take a while...
    Successfully installed json-2.7.1
    Fetching: ruby2_keywords-0.0.5.gem (10752B)
    Successfully installed ruby2_keywords-0.0.5
    Fetching: faraday-retry-1.0.3.gem (10240B)
    Successfully installed faraday-retry-1.0.3
    Fetching: faraday-rack-1.0.0.gem (7168B)
    Successfully installed faraday-rack-1.0.0
    Fetching: faraday-patron-1.0.0.gem (7680B)
    Successfully installed faraday-patron-1.0.0
    Fetching: faraday-net_http_persistent-1.2.0.gem (7680B)
    Successfully installed faraday-net_http_persistent-1.2.0
    Fetching: faraday-net_http-1.0.1.gem (8192B)
    Successfully installed faraday-net_http-1.0.1
    Fetching: multipart-post-2.4.0.gem (15872B)
    Successfully installed multipart-post-2.4.0
    Fetching: faraday-multipart-1.0.4.gem (10752B)
    Successfully installed faraday-multipart-1.0.4
    Fetching: faraday-httpclient-1.0.1.gem (7680B)
    Successfully installed faraday-httpclient-1.0.1
    Fetching: faraday-excon-1.1.0.gem (7168B)
    Successfully installed faraday-excon-1.1.0
    Fetching: faraday-em_synchrony-1.0.0.gem (8192B)
    Successfully installed faraday-em_synchrony-1.0.0
    Fetching: faraday-em_http-1.0.0.gem (9216B)
    Successfully installed faraday-em_http-1.0.0
    Fetching: faraday-1.10.3.gem (71680B)
    Successfully installed faraday-1.10.3
    Fetching: pulpcore_client-3.46.0.gem (182784B)
    Successfully installed pulpcore_client-3.46.0
    15 gems installed
    ```