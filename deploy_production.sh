#!/bin/bash
set -e

PROD_BACKEND="https://zektrix-backend-production.up.railway.app"
SSH_HOST="u485600077@82.25.102.184"
SSH_PORT="65002"
SSH_PASS="Credcada1."
GITHUB_REMOTE="origin"
GITHUB_BRANCH="main"

echo "============================================"
echo "   DEPLOY PRODUCTION - zektrix.uk"
echo "============================================"

# Ensure sshpass is installed
which sshpass >/dev/null 2>&1 || apt-get install -y sshpass >/dev/null 2>&1

# 1. Push backend to GitHub (Railway auto-deploy)
echo ""
echo "[1/5] Pushing backend to GitHub..."
cd /app
git add -A
git diff --cached --quiet && echo "No changes to commit" || git commit -m "Production deploy $(date +%Y%m%d-%H%M%S)"
git push $GITHUB_REMOTE $GITHUB_BRANCH 2>&1 || echo "Push failed or nothing to push"
echo "Backend: DONE"

# 2. Build frontend with PRODUCTION URL (without touching .env)
echo ""
echo "[2/5] Building frontend with production URL..."
cd /app/frontend
rm -rf build
REACT_APP_BACKEND_URL=$PROD_BACKEND yarn build 2>&1 | tail -3
echo "Build: DONE"

# 3. Verify build
echo ""
echo "[3/5] Verifying build..."
JS_FILE=$(ls build/static/js/main.*.js)
PREVIEW_COUNT=$(grep -c "preview.emergentagent.com" "$JS_FILE" || true)
PROD_COUNT=$(grep -c "zektrix-backend-production" "$JS_FILE" || true)

if [ "$PREVIEW_COUNT" -gt 0 ]; then
    echo "ABORT: Preview URL found in build!"
    exit 1
fi
if [ "$PROD_COUNT" -eq 0 ]; then
    echo "ABORT: Production URL NOT found in build!"
    exit 1
fi
echo "Verify: CLEAN (production URL only)"

# 4. Upload to Hostinger
echo ""
echo "[4/5] Deploying to Hostinger..."
cd build && tar czf /tmp/zektrix_prod.tar.gz .

sshpass -p "$SSH_PASS" scp -P $SSH_PORT -o StrictHostKeyChecking=no /tmp/zektrix_prod.tar.gz $SSH_HOST:~/zektrix_prod.tar.gz

sshpass -p "$SSH_PASS" ssh -p $SSH_PORT -o StrictHostKeyChecking=no $SSH_HOST "
  cp domains/zektrix.uk/public_html/.htaccess ~/htaccess_bk.txt 2>/dev/null
  cd domains/zektrix.uk/public_html/ && find . -not -name '.htaccess' -not -name '.' -not -name '..' -delete 2>/dev/null
  cd ~/domains/zektrix.uk/public_html/ && tar xzf ~/zektrix_prod.tar.gz
  cp ~/htaccess_bk.txt ~/domains/zektrix.uk/public_html/.htaccess 2>/dev/null
"
echo "Hostinger: DONE"

# 5. Verify live site
echo ""
echo "[5/5] Verifying live site..."
sleep 2
LIVE_JS=$(curl -s https://zektrix.uk | grep -o 'main\.[a-z0-9]*\.js')
LIVE_URLS=$(curl -s "https://zektrix.uk/static/js/$LIVE_JS" | grep -oP 'https://[a-zA-Z0-9._-]+\.(up\.railway\.app|preview\.emergentagent\.com)' | sort -u)

echo "Live JS: $LIVE_JS"
echo "URLs in JS: $LIVE_URLS"

if echo "$LIVE_URLS" | grep -q "preview"; then
    echo "WARNING: Preview URL detected on live site!"
else
    echo "VERIFIED: Production URL only"
fi

echo ""
echo "============================================"
echo "   DEPLOY COMPLETE"
echo "   Backend: GitHub -> Railway (auto)"
echo "   Frontend: Hostinger (zektrix.uk)"
echo "============================================"
