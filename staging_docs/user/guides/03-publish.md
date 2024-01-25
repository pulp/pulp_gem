# Publish and Host a Repository

This section assumes that you have a repository with content in it.
See [Sync](site:pulp_gem/docs/user/guides/sync/) or [Upload](site:pulp_gem/docs/user/guides/upload/) guides.

## 1. Create a Publication

Kick off a publish task by creating a new publication. The publish task will generate all the
metadata that `gem` needs to install packages (although it will need to be hosted through a
Distribution before it is consumable).

=== "run"
    ```bash
    pulp gem publication create --repository foo --version 1
    ```

    !!! tip
        If `--version` is ommited, Pulp will assume the latest version.
=== "output"
    ```json
    {
      "pulp_href": "/pulp/api/v3/publications/gem/gem/0188e510-cbbe-7586-b182-927bacc89bdb/",
      "pulp_created": "2023-06-22T21:44:23.230932Z",
      "repository_version": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/1/",
      "repository": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/"
    }
    ```


## 2. Host a Publication by creating a Distribution

To host a publication, (which makes it consumable by `gem`), users create a distribution which will serve the associated publication at `/pulp/content/<distribution.base_path>`

=== "run"
    ```bash
    PUBLICATION_HREF=$(pulp gem publication list | jq -r .[0].pulp_href)
    pulp gem distribution create --name foo \
      --base-path foo --publication "$PUBLICATION_HREF"
    ```
=== "output"
    ```json
    {
      "pulp_href": "/pulp/api/v3/distributions/gem/gem/0188e513-594c-7c44-aaff-beed0f97363e/",
      "pulp_created": "2023-06-22T21:47:10.540670Z",
      "base_path": "foo",
      "base_url": "http://localhost:5001/pulp/content/foo/",
      "content_guard": null,
      "hidden": false,
      "pulp_labels": {},
      "name": "foo",
      "repository": null,
      "publication": "/pulp/api/v3/publications/gem/gem/0188e510-cbbe-7586-b182-927bacc89bdb/",
      "remote": null
    }
    ```

!!! note
    Alternatively you could specify the repository when creating a distribution in which case Pulp will automatically distribute the latest available publication for the greatest repository version


## 3. Enable Pull-Through Caching:

Only gems present in your repository will be available from your index, but adding a remote source to
your distribution will enable the pull-through cache feature.

This feature allows you to install any gem from the remote source and have Pulp store that gem as orphaned content.

```bash
pulp gem distribution update --name foo --remote gem
```

!!! warning
    Support for pull-through caching is provided as a tech preview in Pulp 3.
    Functionality may not work or may be incomplete. Also, backwards compatibility when upgrading is not guaranteed.


## 4. Use the newly created distribution

The metadata and packages can now be retrieved from the distribution:

```bash
http $BASE_ADDR/pulp/content/foo/specs.4.8
http $BASE_ADDR/pulp/content/foo/gems/panda-1.1.0.gem
```

The content is now gem installable:

```
gem install --clear-sources --source $BASE_ADDR/pulp/content/foo/ panda
```
