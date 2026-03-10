CONTENT_ORIGIN = "https://pulp:443"
ANSIBLE_API_HOSTNAME = "https://pulp:443"
ANSIBLE_CONTENT_HOSTNAME = "https://pulp:443/pulp/content"
PRIVATE_KEY_PATH = "/etc/pulp/certs/token_private_key.pem"
PUBLIC_KEY_PATH = "/etc/pulp/certs/token_public_key.pem"
TOKEN_SERVER = "https://pulp:443/token/"
TOKEN_SIGNATURE_ALGORITHM = "ES256"
CACHE_ENABLED = True
REDIS_HOST = "localhost"
REDIS_PORT = 6379
ANALYTICS = False

API_ROOT = "/rerouted/djnd/"


MEDIA_ROOT = ""
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": "AKIAIT2Z5TDYPX3ARJBA",
            "addressing_style": "path",
            "bucket_name": "pulp3",
            "default_acl": "@none",
            "endpoint_url": "http://minio:9000",
            "region_name": "eu-central-1",
            "secret_key": "fqRvjWaPU5o0fCqQuUWbj9Fainj2pVZtBCiDiieS",
            "signature_version": "s3v4",
        },
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
ALLOWED_CONTENT_CHECKSUMS = ["md5", "sha224", "sha256", "sha384", "sha512"]
DOMAIN_ENABLED = True
