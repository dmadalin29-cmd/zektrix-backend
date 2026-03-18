#!/bin/bash
set -e

PROD_BACKEND="https://zektrix-backend-production.up.railway.app"
SSH_HOST="u485600077@82.25.102.184"
SSH_PORT="65002"
SSH_PASS="Credcada1."

echo "============================================"
echo "   DEPLOY PRODUCTION - zektrix.uk"
echo "============================================"

which sshpass >/dev/null 2>&1 || apt-get install -y sshpass >/dev/null 2>&1

# 1. Push backend to GitHub
echo ""
echo "[1/5] Pushing to GitHub..."
cd /app
git add -A
git diff --cached --quiet && echo "No changes" || git commit -m "Production deploy $(date +%Y%m%d-%H%M%S)"
git push origin main 2>&1 || echo "Nothing to push"

# 2. Build frontend - MODIFY .env temporarily
echo ""
echo "[2/5] Building frontend..."
cd /app/frontend
cp .env .env.dev.bak
cat > .env << EOF
REACT_APP_BACKEND_URL=$PROD_BACKEND
WDS_SOCKET_PORT=443
EOF
rm -rf build
yarn build 2>&1 | tail -2
cp .env.dev.bak .env
rm -f .env.dev.bak

# 3. Verify
echo ""
echo "[3/5] Verifying..."
JS_FILE=$(ls build/static/js/main.*.js)
if grep -q "preview.emergentagent.com" "$JS_FILE"; then
    echo "ABORT: Preview URL in build!"
    exit 1
fi
if ! grep -q "zektrix-backend-production" "$JS_FILE"; then
    echo "ABORT: Production URL missing!"
    exit 1
fi
echo "Build verified: production URL only"

# 4. Deploy to Hostinger
echo ""
echo "[4/5] Deploying to Hostinger..."
cd build && tar czf /tmp/zektrix_deploy.tar.gz .
sshpass -p "$SSH_PASS" scp -P $SSH_PORT -o StrictHostKeyChecking=no /tmp/zektrix_deploy.tar.gz $SSH_HOST:~/zektrix_deploy.tar.gz
sshpass -p "$SSH_PASS" ssh -p $SSH_PORT -o StrictHostKeyChecking=no $SSH_HOST "
  cp domains/zektrix.uk/public_html/.htaccess ~/htaccess_bk.txt 2>/dev/null
  cd domains/zektrix.uk/public_html/ && find . -not -name '.htaccess' -not -name '.' -not -name '..' -delete 2>/dev/null
  tar xzf ~/zektrix_deploy.tar.gz
  cp ~/htaccess_bk.txt .htaccess 2>/dev/null
"

# 5. Verify live
echo ""
echo "[5/5] Verifying live..."
sleep 2
LIVE_JS=$(curl -s https://zektrix.uk | grep -o 'main\.[a-z0-9]*\.js')
if curl -s "https://zektrix.uk/static/js/$LIVE_JS" | grep -q "preview.emergentagent.com"; then
    echo "WARNING: Preview URL on live site!"
else
    echo "LIVE VERIFIED: production URL only"
fi

echo ""
echo "============================================"
echo "   DEPLOY COMPLETE"
echo "   Backend: GitHub -> Railway"
echo "   Frontend: Hostinger (zektrix.uk)"
echo "============================================"
