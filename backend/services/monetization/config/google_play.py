"""
Google Play API Client Configuration

This sets up authentication with Google Play Developer API
to validate purchase receipts.

Setup Required:
1. Create a service account in Google Cloud Console
2. Enable Google Play Developer API
3. Download JSON key file
4. Grant API access in Google Play Console
5. Set GOOGLE_APPLICATION_CREDENTIALS environment variable

Security Note:
- Keep service account JSON file secure (never commit to git)
- Use environment variables for credentials
- Restrict API access to only what's needed
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional

class GooglePlayClient:
    """
    Wrapper for Google Play Developer API
    """
    
    def __init__(self):
        """
        Initialize the Google Play API client
        
        Reads credentials from environment variable:
        GOOGLE_APPLICATION_CREDENTIALS = path to service account JSON
        """
        self.package_name = os.getenv("ANDROID_PACKAGE_NAME", "com.yourcompany.wordwars")
        
        # Path to service account JSON file
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not credentials_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                "Please set it to the path of your service account JSON file."
            )
        
        # Load credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/androidpublisher"]
        )
        
        # Build the API client
        self.service = build("androidpublisher", "v3", credentials=self.credentials)
    
    def verify_purchase(self, product_id: str, purchase_token: str) -> dict:
        """
        Verify a product purchase with Google Play
        
        Args:
            product_id: The product ID (e.g., "com.wordwars.hints_10")
            purchase_token: The purchase token from Unity IAP
        
        Returns:
            dict: Purchase details from Google Play API
            
        Raises:
            Exception: If verification fails
        """
        try:
            # Call Google Play API to get purchase details
            result = self.service.purchases().products().get(
                packageName=self.package_name,
                productId=product_id,
                token=purchase_token
            ).execute()
            
            return result
            
        except Exception as e:
            print(f"❌ Google Play verification failed: {e}")
            raise
    
    def verify_subscription(self, subscription_id: str, purchase_token: str) -> dict:
        """
        Verify a subscription purchase with Google Play
        
        Args:
            subscription_id: The subscription ID
            purchase_token: The purchase token from Unity IAP
        
        Returns:
            dict: Subscription details from Google Play API
        """
        try:
            result = self.service.purchases().subscriptions().get(
                packageName=self.package_name,
                subscriptionId=subscription_id,
                token=purchase_token
            ).execute()
            
            return result
            
        except Exception as e:
            print(f"❌ Google Play subscription verification failed: {e}")
            raise


# Singleton instance
_google_play_client: Optional[GooglePlayClient] = None

def get_google_play_client() -> GooglePlayClient:
    """
    Get or create the Google Play API client singleton
    """
    global _google_play_client
    if _google_play_client is None:
        _google_play_client = GooglePlayClient()
    return _google_play_client
