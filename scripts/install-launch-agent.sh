#!/bin/bash
# Install Roon Bridge as macOS LaunchAgent (auto-start at login)
# Usage: ./scripts/install-launch-agent.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../" && pwd)"
BRIDGE_DIR="$PROJECT_DIR/roon-bridge"
AGENT_NAME="com.aime.roon-bridge"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/$AGENT_NAME.plist"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  Installing Roon Bridge LaunchAgent${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# Créer le répertoire LaunchAgents s'il n'existe pas
mkdir -p "$LAUNCH_AGENTS_DIR"

# Créer le fichier plist
echo "📝 Creating LaunchAgent plist..."

cat > "$PLIST_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aime.roon-bridge</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/node</string>
        <string>BRIDGE_DIR/app.js</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>BRIDGE_DIR</string>
    
    <key>StandardOutPath</key>
    <string>/tmp/aime_bridge.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/aime_bridge.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StartInterval</key>
    <integer>10</integer>
    
    <key>ThrottleInterval</key>
    <integer>5</integer>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>ROON_BRIDGE_PORT</key>
        <string>3330</string>
        <key>CONFIG_DIR</key>
        <string>PROJECT_DIR/config</string>
    </dict>
</dict>
</plist>
EOF

# Remplacer les variables
sed -i '' "s|BRIDGE_DIR|$BRIDGE_DIR|g" "$PLIST_FILE"
sed -i '' "s|PROJECT_DIR|$PROJECT_DIR|g" "$PLIST_FILE"

echo -e "${GREEN}✓ Created $PLIST_FILE${NC}"
echo ""

# Charger l'agent
echo "🔌 Loading LaunchAgent..."
launchctl load "$PLIST_FILE" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  LaunchAgent may already be loaded, unloading first...${NC}"
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    sleep 1
    launchctl load "$PLIST_FILE"
}

echo -e "${GREEN}✓ LaunchAgent loaded${NC}"
echo ""

# Vérifier que le service est chargé
if launchctl list | grep -q "$AGENT_NAME"; then
    echo -e "${GREEN}✅ Roon Bridge installed and running!${NC}"
    echo ""
    echo "📋 Status:"
    echo "   Label:      $AGENT_NAME"
    echo "   Plist:      $PLIST_FILE"
    echo "   Log:        /tmp/aime_bridge.log"
    echo "   Auto-start: ✓ Enabled at login"
    echo ""
    echo "🔧 Commands:"
    echo "   Check status:   launchctl list | grep roon-bridge"
    echo "   View logs:      tail -f /tmp/aime_bridge.log"
    echo "   Reload:         launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
    echo "   Uninstall:      rm $PLIST_FILE && launchctl unload $PLIST_FILE 2>/dev/null"
else
    echo -e "${RED}❌ Failed to load LaunchAgent${NC}"
    echo ""
    echo "Try manually:"
    echo "  launchctl load $PLIST_FILE"
    exit 1
fi
