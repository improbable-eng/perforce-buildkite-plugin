# Insecure SSL

Don't use this in production.

These files were generated via

```bash
mkdir -p "python/fixture/insecure-ssl"
chmod 700 "python/fixture/insecure-ssl"
P4SSLDIR="python/fixture/insecure-ssl" p4d -Gc
P4SSLDIR="python/fixture/insecure-ssl" p4d -Gf
```

... and they're for use within the SSL-using tests.
