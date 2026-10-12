#!/bin/bash
# Helper script to encode Firebase credentials to base64

FIREBASE_JSON_PATH="$1"

if [ -z "$FIREBASE_JSON_PATH" ]; then
    echo "Usage: ./encode_firebase_credentials.sh <path-to-firebase-json>"
    echo ""
    echo "Example:"
    echo "  ./encode_firebase_credentials.sh ~/Downloads/aiwordwars-firebase-adminsdk-fbsvc-e1d4a67975.json"
    exit 1
fi

if [ ! -f "$FIREBASE_JSON_PATH" ]; then
    echo "Error: File not found: $FIREBASE_JSON_PATH"
    exit 1
fi

echo "Encoding Firebase credentials to base64..."
echo ""
echo "==== BASE64 ENCODED CREDENTIALS ===="
base64 -i "$FIREBASE_JSON_PATH"
echo ""
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Copy the base64 string above (the long string between the ==== lines)"
echo "2. Go to: https://github.com/ADARSHKUMAR2/AIWordWars_BE/settings/secrets/actions"
echo "3. Click 'New repository secret'"
echo "4. Name: FIREBASE_CREDENTIALS_BASE64"
echo "5. Value: Paste the base64 string"
echo "6. Click 'Add secret'"
echo "7. Go to Actions tab and trigger 'Deploy Microservices to Cloud Run'"
echo ""
