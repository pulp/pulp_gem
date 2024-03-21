# Using Custom Certificates

When using Pulp as mirror of `rubygems.org`, you may need to configure `bundler` to use custom SSL certificates.
Any certificate related settings for `bundler` need to be also added for `gem`.
If only `bundler` is configured, metadata will be downloaded from Pulp, but gems will fail to download.
Gems are downloaded by `gem` and it has its own configuration.
