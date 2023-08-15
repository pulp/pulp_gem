=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://docs.pulpproject.org/en/3.0/nightly/contributing/git.html#changelog-update

    WARNING: Don't drop the next directive!

.. towncrier release notes start

0.2.0 (2023-08-15)
==================

Features
--------

- Added support for gems with a platform that is not "ruby".
  `#130 <https://github.com/pulp/pulp_gem/issues/130>`__


Bugfixes
--------

- Fixed the detection of prerelease versions.
  `#114 <https://github.com/pulp/pulp_gem/issues/114>`__
- Added a datarepair-gemspec-platform command to regenerate the gemspec artifacts and properly set the platform attribute on existing gems.
  `#130 <https://github.com/pulp/pulp_gem/issues/130>`__
- Fixed the generation of gemspec data.
  `#131 <https://github.com/pulp/pulp_gem/issues/131>`__


----


0.1.1 (2023-06-29)
==================

Bugfixes
--------

- Fixed the detection of prerelease versions.
  `#114 <https://github.com/pulp/pulp_gem/issues/114>`__


----


0.1.0 (2023-06-26)
==================

Features
--------

- Added support for pull-through caching. Add a remote to a distribution to enable this feature.
  `#94 <https://github.com/pulp/pulp_gem/issues/94>`__
- Implemented new synching and publishing the compact index format.
  Rubymarshal and quick index will still be generated when publishing, but synching is exclusive to the new format.
  Added checksum and dependency information to gem content.
  Added ``prereleases`` and ``includes`` / ``excludes`` filter to remotes.
  `#96 <https://github.com/pulp/pulp_gem/issues/96>`__
- Added compatibility for pulpcore 3.25, pulpcore support is now >=3.25,<3.40.
  `#99 <https://github.com/pulp/pulp_gem/issues/99>`__
- Added support to assign a remote to a repository.
  `#101 <https://github.com/pulp/pulp_gem/issues/101>`__


Bugfixes
--------

- Optimized publish task to be significantly faster.
  `#93 <https://github.com/pulp/pulp_gem/issues/93>`__


Improved Documentation
----------------------

- Added CLI commands to documented workflows.
  `#107 <https://github.com/pulp/pulp_gem/issues/107>`__


Deprecations and Removals
-------------------------

- Disabled synching without compact index format.
  Existing content will still be downloadable.
  There is a ``pulpcore-manager datarepair-shallow-gems`` command that will reindex content to the new format given their artifacts are persisted.
  `#96 <https://github.com/pulp/pulp_gem/issues/96>`__


----


0.0.1b3 (2022-03-01)
====================

Misc
----

- `#39 <https://github.com/pulp/pulp_gem/issues/39>`__


----


0.0.1b2 (2018-12-19)
====================

No significant changes.
