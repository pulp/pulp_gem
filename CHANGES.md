# Changelog

[//]: # (You should *NOT* be adding new change log entries to this file, this)
[//]: # (file is managed by towncrier. You *may* edit previous change logs to)
[//]: # (fix problems like typo corrections or such.)
[//]: # (To add a new change log entry, please see the contributing docs.)
[//]: # (WARNING: Don't drop the towncrier directive!)

[//]: # (towncrier release notes start)

## 0.7.1 (2025-03-28) {: #0.7.1 }

#### Misc {: #0.7.1-misc }

- 

---

## 0.7.0 (2025-03-18) {: #0.7.0 }

#### Bugfixes {: #0.7.0-bugfix }

- Fixed handling somewhat inconsistent metadata on rubygems.org where an md5 checksum is missing in the versions file.
  [#313](https://github.com/pulp/pulp_gem/issues/313)
- Allowed pulp-glue-gem version 0.5.* to be installed.

#### Deprecations and Removals {: #0.7.0-removal }

- Squashed and rebased old migrations (before the 0.4 release) to prepare for pulpcore 3.70 compatibility.
  [#334](https://github.com/pulp/pulp_gem/issues/334)

#### Misc {: #0.7.0-misc }

- [#339](https://github.com/pulp/pulp_gem/issues/339)

---

## 0.6.2 (2025-02-10) {: #0.6.2 }

#### Misc {: #0.6.2-misc }

- [#339](https://github.com/pulp/pulp_gem/issues/339)

---

## 0.6.1 (2024-06-26) {: #0.6.1 }


#### Bugfixes {: #0.6.1-bugfix }

- Allowed pulp-glue-gem version 0.5.* to be installed.

---

## 0.6.0 (2024-06-19) {: #0.6.0 }


#### Deprecations and Removals {: #0.6.0-removal }

- Bumped miminal pulpcore requirement to 3.49.0.
- Droped support for python 3.8.

#### Misc {: #0.6.0-misc }

- 

---

## 0.5.1 (2024-05-23) {: #0.5.1 }

### Bugfixes

-   Fixed the wrong upper bound for pulpcore version requirement.
    [#265](https://github.com/pulp/pulp_gem/issues/265)

---

## 0.5.0 (2024-02-12) {: #0.5.0 }

### Features

-   Added replica definitions.
    [#216](https://github.com/pulp/pulp_gem/issues/216)

### Bugfixes

-   Fixed a bug where legacy gems would cause an exception in pulpcore-content.
    [#209](https://github.com/pulp/pulp_gem/issues/209)

### Deprecations and Removals

-   Bumped the requirement on pulpcore to >=3.39 as the next supported version in the line.

---

## 0.4.1 (2024-02-12) {: #0.4.1 }

### Bugfixes

-   Fixed a bug where legacy gems would cause an exception in pulpcore-content.
    [#209](https://github.com/pulp/pulp_gem/issues/209)

---

## 0.4.0 (2023-11-03) {: #0.4.0 }

### Features

-   Bumped pulpcore compatibility to 3.54.
-   Added support for RBAC and domains.
    [#154](https://github.com/pulp/pulp_gem/issues/154)

### Deprecations and Removals

-   Removed pre 0.2 residua. When you are upgrading from <0.3, and your system was operated on <0.2 before, make sure you have run the corresponding datarepair commands before upgrading the codebase to this version.
    [#143](https://github.com/pulp/pulp_gem/issues/143)

---

## 0.3.0 (2023-09-18) {: #0.3.0 }

### Deprecations and Removals

-   Added a migration to tell admins to run certain datarepair commands before upgrading to 0.4.
    [#141](https://github.com/pulp/pulp_gem/issues/141)

---

## 0.2.0 (2023-08-15) {: #0.2.0 }

### Features

-   Added support for gems with a platform that is not "ruby".
    [#130](https://github.com/pulp/pulp_gem/issues/130)

### Bugfixes

-   Fixed the detection of prerelease versions.
    [#114](https://github.com/pulp/pulp_gem/issues/114)
-   Added a datarepair-gemspec-platform command to regenerate the gemspec artifacts and properly set the platform attribute on existing gems.
    [#130](https://github.com/pulp/pulp_gem/issues/130)
-   Fixed the generation of gemspec data.
    [#131](https://github.com/pulp/pulp_gem/issues/131)

---

## 0.1.1 (2023-06-29) {: #0.1.1 }

### Bugfixes

-   Fixed the detection of prerelease versions.
    [#114](https://github.com/pulp/pulp_gem/issues/114)

---

## 0.1.0 (2023-06-26) {: #0.1.0 }

### Features

-   Added support for pull-through caching. Add a remote to a distribution to enable this feature.
    [#94](https://github.com/pulp/pulp_gem/issues/94)
-   Implemented new synching and publishing the compact index format.
    Rubymarshal and quick index will still be generated when publishing, but synching is exclusive to the new format.
    Added checksum and dependency information to gem content.
    Added `prereleases` and `includes` / `excludes` filter to remotes.
    [#96](https://github.com/pulp/pulp_gem/issues/96)
-   Added compatibility for pulpcore 3.25, pulpcore support is now >=3.25,<3.40.
    [#99](https://github.com/pulp/pulp_gem/issues/99)
-   Added support to assign a remote to a repository.
    [#101](https://github.com/pulp/pulp_gem/issues/101)

### Bugfixes

-   Optimized publish task to be significantly faster.
    [#93](https://github.com/pulp/pulp_gem/issues/93)

### Improved Documentation

-   Added CLI commands to documented workflows.
    [#107](https://github.com/pulp/pulp_gem/issues/107)

### Deprecations and Removals

-   Disabled synching without compact index format.
    Existing content will still be downloadable.
    There is a `pulpcore-manager datarepair-shallow-gems` command that will reindex content to the new format given their artifacts are persisted.
    [#96](https://github.com/pulp/pulp_gem/issues/96)

---

## 0.0.1b3 (2022-03-01)

### Misc

-   [#39](https://github.com/pulp/pulp_gem/issues/39)

---

## 0.0.1b2 (2018-12-19)

No significant changes.
