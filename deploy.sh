#!/bin/bash
# deploy.sh - Builds frontend with PRODUCTION URL and deploys to Hostinger
# Usage: bash /app/deploy.sh

set -e

PROD_URL="https://zektrix-backend-production.up.railway.app"
SSH_HOST="u485600077@82.25.102.184"
SSH_PORT="65002"
SSH_PASS="Credcada1."

echo "=== DEPLOYING TO PRODUCTION ==="

# Step 1: Force production URL in .env for build
cd /app/frontend
cp .env .env.dev.backup
echo "REACT_APP_BACKEND_URL=$PROD_URL" > .env
echo "WDS_SOCKET_PORT=443" >> .env

# Step 2: Build
echo "Building..."
REACT_APP_BACKEND_URL=$PROD_URL yarn build 2>&1 | tail -3

# Step 3: Restore dev .env
cp .env.dev.backup .env

# Step 4: Verify build has correct URL
FOUND=$(grep -o "$PROD_URL" build/static/js/main.*.js | head -1)
if [ -z "$FOUND" ]; then
    echo "ERROR: Production URL NOT found in build! Aborting."
    exit 1
fi
echo "Build verified: $PROD_URL"

# Step 5: Deploy to Hostinger
cd build && tar czf /tmp/build.tar.gz .
sshpass -p "$SSH_PASS" scp -P $SSH_PORT -o StrictHostKeyChecking=no /tmp/build.tar.gz $SSH_HOST:~/build.tar.gz
sshpass -p "$SSH_PASS" ssh -p $SSH_PORT -o StrictHostKeyChecking=no $SSH_HOST "
cp domains/zektrix.uk/public_html/.htaccess ~/htaccess_bk.txt 2>/dev/null
cd domains/zektrix.uk/public_html/ && rm -rf static asset-manifest.json favicon.png index.html manifest.json robots.txt sw.js icon-* sitemap*
cd ~/domains/zektrix.uk/public_html/ && tar xzf ~/build.tar.gz
cp ~/htaccess_bk.txt ~/domains/zektrix.uk/public_html/.htaccess 2>/dev/null
"

# Step 6: Verify live site
sleep 2
LIVE_JS=$(curl -s https://zektrix.uk | grep -o 'static/js/main[^"]*\.js')
LIVE_URL=$(curl -s "https://zektrix.uk/$LIVE_JS" | grep -o "\"$PROD_URL" | head -1)
if [ -z "$LIVE_URL" ]; then
    echo "WARNING: Could not verify live site URL"
else
    echo "LIVE SITE VERIFIED: $PROD_URL"
fi

echo "=== DEPLOY COMPLETE ==="
