# Insecure SSL

Cert for use in unit tests.

Do not use in production.

Generated via:

```bash
mkdir -p "python/fixture/insecure-ssl"
chmod 700 "python/fixture/insecure-ssl"
P4SSLDIR="python/fixture/insecure-ssl" p4d -Gc
P4SSLDIR="python/fixture/insecure-ssl" p4d -Gf
```
