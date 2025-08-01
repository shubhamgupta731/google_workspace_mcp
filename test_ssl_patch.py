#!/usr/bin/env python3
"""Test script to verify SSL patch functionality with custom CA bundle."""

import os
import sys
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing SSL patch for Google Workspace MCP...")
print("-" * 60)

# Test 1: Test without CA bundle
print("\n1. Testing without CUSTOM_CA_BUNDLE...")
if 'CUSTOM_CA_BUNDLE' in os.environ:
    del os.environ['CUSTOM_CA_BUNDLE']

from auth.ssl_patch import apply_ssl_patch
result = apply_ssl_patch()
print(f"   {'✓' if result else '✗'} SSL patch applied: {result}")
print("   ℹ  No custom CA bundle configured (expected behavior)")

# Test 2: Test with non-existent CA bundle
print("\n2. Testing with non-existent CA bundle...")
os.environ['CUSTOM_CA_BUNDLE'] = '/tmp/non-existent-bundle.pem'
result = apply_ssl_patch()
print(f"   {'✓' if not result else '✗'} SSL patch correctly failed for non-existent file")

# Test 3: Test with valid CA bundle
print("\n3. Testing with valid CA bundle...")
# Create a temporary CA bundle for testing
with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_bundle:
    # Find system certificates
    system_cert_locations = [
        '/etc/ssl/certs/ca-certificates.crt',  # Debian/Ubuntu
        '/etc/pki/tls/certs/ca-bundle.crt',    # RedHat/CentOS
        '/etc/ssl/cert.pem',                    # macOS/BSD
        '/System/Library/OpenSSL/certs/cert.pem',  # macOS alternate
    ]
    
    cert_found = False
    for cert_location in system_cert_locations:
        if os.path.exists(cert_location):
            with open(cert_location, 'r') as f:
                temp_bundle.write(f.read())
            print(f"   ✓ Created test CA bundle using: {cert_location}")
            cert_found = True
            break
    
    if not cert_found:
        print("   ✗ No system certificates found, using dummy certificate")
        # Write a dummy certificate for testing
        temp_bundle.write("-----BEGIN CERTIFICATE-----\nDUMMY\n-----END CERTIFICATE-----\n")
    
    temp_bundle_path = temp_bundle.name

os.environ['CUSTOM_CA_BUNDLE'] = temp_bundle_path
result = apply_ssl_patch()
print(f"   {'✓' if result else '✗'} SSL patch applied with custom CA bundle: {temp_bundle_path}")

# Test 4: Verify httplib2 patching
print("\n4. Verifying httplib2 patch...")
try:
    import httplib2
    
    # Create an Http object (should use our patched version)
    http = httplib2.Http()
    
    # Check if ca_certs points to our bundle
    if hasattr(http, 'ca_certs') and http.ca_certs == temp_bundle_path:
        print(f"   ✓ httplib2.Http.ca_certs correctly set to: {http.ca_certs}")
    else:
        print(f"   ✗ httplib2.Http.ca_certs not set correctly")
    
except ImportError:
    print("   ℹ  httplib2 not installed (test skipped)")

# Test 5: Verify environment variables
print("\n5. Verifying SSL environment variables...")
expected_vars = ['REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSL_CERT_FILE']
for var in expected_vars:
    value = os.environ.get(var)
    if value == temp_bundle_path:
        print(f"   ✓ {var} = {value}")
    else:
        print(f"   ✗ {var} not set correctly (got: {value})")

# Test 6: Test actual HTTPS connection (if system certs were found)
if cert_found:
    print("\n6. Testing HTTPS connection to Google OAuth2...")
    try:
        import httplib2
        
        # Create an Http object (should use our patched version)
        http = httplib2.Http()
        
        # Try to connect to Google OAuth2 endpoint
        resp, content = http.request("https://oauth2.googleapis.com/.well-known/openid-configuration", "GET")
        
        print(f"   ✓ Successfully connected to oauth2.googleapis.com")
        print(f"   ✓ Response status: {resp.status}")
        print(f"   ✓ Response length: {len(content)} bytes")
        
    except Exception as e:
        print(f"   ✗ Failed to connect: {e}")
else:
    print("\n6. Skipping HTTPS test (no valid system certificates found)")

# Test 7: Test Google API client imports
print("\n7. Testing Google API client imports...")
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    print("   ✓ Google API client imports successful")
except Exception as e:
    print(f"   ✗ Failed to import Google API clients: {e}")

# Cleanup
print("\n8. Cleanup...")
try:
    os.unlink(temp_bundle_path)
    print(f"   ✓ Cleaned up temporary CA bundle: {temp_bundle_path}")
except Exception as e:
    print(f"   ✗ Failed to cleanup: {e}")

print("\n" + "=" * 60)
print("Test completed!")
print("\nTo use with your own CA bundle:")
print(f"  export CUSTOM_CA_BUNDLE=/path/to/your/ca-bundle.pem")
print(f"  uvx workspace-mcp")