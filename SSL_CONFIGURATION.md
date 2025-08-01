# SSL/TLS Configuration for Custom CA Bundles

This guide explains how to configure the Google Workspace MCP server to work with custom Certificate Authorities (CAs), such as those used by corporate VPNs or security solutions.

## Overview

The Google Workspace MCP server supports using custom CA bundles for SSL/TLS verification. This is useful when:
- You're behind a corporate firewall/VPN that uses custom certificates
- You're using security solutions like Cato Networks, Zscaler, or similar
- You need to add additional trusted CAs beyond system defaults

## Configuration

### 1. Create Your Combined CA Bundle

First, create a combined CA bundle file that includes both system certificates and your custom certificates:

```bash
# Example: Combine system certs with corporate certs
cat /etc/ssl/certs/ca-certificates.crt ~/.corporate/custom-ca.pem > ~/combined-ca-bundle.pem
```

### 2. Configure MCP Server

When adding the Google Workspace MCP server to your MCP client, set the `CUSTOM_CA_BUNDLE` environment variable:

#### Using Claude Desktop

In your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "uvx",
      "args": ["workspace-mcp"],
      "env": {
        "CUSTOM_CA_BUNDLE": "/Users/yourname/combined-ca-bundle.pem"
      }
    }
  }
}
```

#### Using Environment Variables

```bash
export CUSTOM_CA_BUNDLE=/path/to/your/combined-ca-bundle.pem
uvx workspace-mcp
```

#### Using Docker

```bash
docker run -p 8000:8000 \
  -e CUSTOM_CA_BUNDLE=/certs/combined-ca-bundle.pem \
  -v /path/to/your/combined-ca-bundle.pem:/certs/combined-ca-bundle.pem:ro \
  -v $(pwd):/app \
  workspace-mcp --transport streamable-http
```

## How It Works

When `CUSTOM_CA_BUNDLE` is set:

1. The SSL patch module loads early, before any Google API imports
2. It configures httplib2 to use your custom CA bundle
3. It sets standard SSL environment variables (`REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, etc.)
4. All subsequent HTTPS connections will use your custom CA bundle

## Creating CA Bundles for Common Scenarios

### Cato Networks
```bash
# Combine system certs with Cato certs
cat /etc/ssl/cert.pem ~/.cato/*.pem > ~/cato-ca-bundle.pem
export CUSTOM_CA_BUNDLE=~/cato-ca-bundle.pem
```

### Zscaler
```bash
# Get Zscaler root certificate and combine with system certs
cat /etc/ssl/certs/ca-certificates.crt ~/Downloads/ZscalerRootCA.pem > ~/zscaler-ca-bundle.pem
export CUSTOM_CA_BUNDLE=~/zscaler-ca-bundle.pem
```

### Corporate Proxy
```bash
# Combine system certs with corporate CA
cat /etc/ssl/cert.pem /usr/local/share/ca-certificates/corporate-ca.crt > ~/corporate-ca-bundle.pem
export CUSTOM_CA_BUNDLE=~/corporate-ca-bundle.pem
```

## Troubleshooting

### Verify CA Bundle
```bash
# Check if your CA bundle is valid
openssl crl2pkcs7 -nocrl -certfile ~/combined-ca-bundle.pem | openssl pkcs7 -print_certs -noout
```

### Test SSL Connection
```python
# Test script to verify SSL configuration
import os
os.environ['CUSTOM_CA_BUNDLE'] = '/path/to/your/combined-ca-bundle.pem'

from auth.ssl_patch import apply_ssl_patch
apply_ssl_patch()

import httplib2
http = httplib2.Http()
resp, content = http.request("https://oauth2.googleapis.com/.well-known/openid-configuration", "GET")
print(f"Status: {resp.status}")
```

### Common Issues

1. **Certificate not found**: Ensure the path in `CUSTOM_CA_BUNDLE` is absolute and the file exists
2. **SSL verification still fails**: Make sure your CA bundle includes all necessary intermediate certificates
3. **Different behavior between tools**: Some tools may need additional configuration beyond the environment variables

## Security Considerations

- Keep your CA bundle file secure and readable only by your user
- Regularly update your CA bundle when certificates change
- Only include CAs that you explicitly trust
- Consider using separate CA bundles for different environments (dev/prod)