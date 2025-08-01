"""SSL certificate patch for custom CA bundle support.

This module provides SSL certificate patching to handle environments where
custom CA certificates need to be used for proper SSL verification.
The CA bundle should be created externally and provided via environment variable.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def patch_httplib2_with_custom_ca(ca_bundle_path: str) -> bool:
    """Patch httplib2 to use a custom CA bundle.
    
    Args:
        ca_bundle_path: Path to the custom CA bundle file
        
    Returns:
        bool: True if patch was successful, False otherwise
    """
    if not os.path.exists(ca_bundle_path):
        logger.error(f"CA bundle not found at: {ca_bundle_path}")
        return False
    
    # Method 1: Set environment variables that many libraries respect
    os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle_path
    os.environ['CURL_CA_BUNDLE'] = ca_bundle_path
    os.environ['SSL_CERT_FILE'] = ca_bundle_path
    logger.info(f"Set SSL certificate environment variables to: {ca_bundle_path}")
    
    # Method 2: Patch httplib2 if it's available
    try:
        import httplib2
        
        # Store the original Http class
        original_http_class = httplib2.Http
        
        class PatchedHttp(original_http_class):
            """Patched Http class that uses custom CA bundle."""
            
            def __init__(self, *args, **kwargs):
                # Initialize the parent class
                super().__init__(*args, **kwargs)
                
                # Override the ca_certs to use our custom bundle
                self.ca_certs = ca_bundle_path
                
                # Ensure SSL certificate validation is enabled
                if hasattr(self, 'disable_ssl_certificate_validation'):
                    self.disable_ssl_certificate_validation = False
        
        # Replace the Http class in httplib2
        httplib2.Http = PatchedHttp
        logger.info(f"httplib2 patched to use CA bundle: {ca_bundle_path}")
        return True
        
    except ImportError:
        logger.info("httplib2 not installed, relying on environment variables for SSL configuration")
        return True
    except Exception as e:
        logger.error(f"Failed to patch httplib2: {e}")
        return False


def apply_ssl_patch() -> bool:
    """Apply SSL patch if configured via environment variable.
    
    Looks for CUSTOM_CA_BUNDLE environment variable containing the path
    to a custom CA bundle file.
    
    Returns:
        bool: True if patch was applied successfully or not needed, False on error
    """
    ca_bundle_path = os.environ.get('CUSTOM_CA_BUNDLE')
    
    if not ca_bundle_path:
        logger.debug("CUSTOM_CA_BUNDLE not set, no SSL patching applied")
        return True
    
    logger.info(f"CUSTOM_CA_BUNDLE set to: {ca_bundle_path}")
    return patch_httplib2_with_custom_ca(ca_bundle_path)


# For backward compatibility, check if SSL patching should be applied
CUSTOM_CA_BUNDLE = os.environ.get('CUSTOM_CA_BUNDLE')
if CUSTOM_CA_BUNDLE:
    logger.info(f"Custom CA bundle configured: {CUSTOM_CA_BUNDLE}")