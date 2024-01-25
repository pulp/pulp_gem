# Upload and Manage Content

## 1. Create a Repository

Start by creating a new repository named "foo".

=== "run"
    ```bash
    pulp gem repository create --name foo
    ```
=== "output"
    ```json
    {
      "pulp_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/",
      "pulp_created": "2023-06-22T20:54:27.113947Z",
      "versions_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/",
      "pulp_labels": {},
      "latest_version_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/0/",
      "name": "foo",
      "description": null,
      "retain_repo_versions": null,
      "remote": null
    }
    ```

## 2. Upload a file to Pulp

Each artifact in Pulp represents a file. They can be created during sync or created manually by uploading a file

=== "run"
    ```bash
    #  Get a Gem package or choose your own and upload to Pulp
    curl -O https://fixtures.pulpproject.org/gem/gems/amber-1.0.0.gem
    pulp gem content upload --file "amber-1.0.0.gem"
    CONTENT_HREF=$(pulp gem content list | jq -r .[0].pulp_href)
    ```
=== "output"
    ```json
    {
      "pulp_href": "/pulp/api/v3/content/gem/gem/0188e53f-b8ae-71e8-a2da-a1c79ab9d822/",
      "pulp_created": "2023-06-22T22:35:38.543295Z",
      "artifacts": {
        "gems/amber-1.0.0.gem": "/pulp/api/v3/artifacts/0188e53f-b84e-74c9-a82e-60583c0e4fd2/",
        "quick/Marshal.4.8/amber-1.0.0.gemspec.rz": "/pulp/api/v3/artifacts/0188e53f-b8aa-7d05-8dd2-1b941fef9b6e/"
      },
      "name": "amber",
      "version": "1.0.0",
      "prerelease": false,
      "dependencies": {},
      "required_ruby_version": ">= 0",
      "required_rubygems_version": ">= 0"
    }
    ```

!!! note
    You can also specify a repository during an upload to immediately add the uploaded content to the repository.

## 3. Add content to a repository

Once there is a content unit, it can be added and removed from repositories using the add and remove commands.
This will create a new `repository version`.

=== "run"
    ```bash
    pulp gem repository content add --repository foo --href $CONTENT_HREF
    pulp gem repository version show --repository foo
    ```
=== "output"
    ```json
    {
      "pulp_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/2/",
      "pulp_created": "2023-06-22T22:54:09.911372Z",
      "number": 2,
      "repository": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/",
      "base_version": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/1/",
      "content_summary": {
        "added": {
          "gem.gem": {
            "count": 1,
            "href": "/pulp/api/v3/content/gem/gem/?repository_version_added=/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/2/"
          }
        },
        "removed": {},
        "present": {
          "gem.gem": {
            "count": 34,
            "href": "/pulp/api/v3/content/gem/gem/?repository_version=/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/2/"
          }
        }
      }
    }
    ```
