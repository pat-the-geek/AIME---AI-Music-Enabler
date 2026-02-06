#!/bin/bash

echo "🔄 Monitoring enrichment progress..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do 
  TIMESTAMP=$(date '+%H:%M:%S')
  echo -n "$TIMESTAMP - "
  
  # Get latest description count
  LAST_DESC=$(grep "descriptions:" /tmp/backend_enrichment.log | tail -1 | grep -o "[0-9]*/236")
  if [ -n "$LAST_DESC" ]; then
    echo "📊 $LAST_DESC"
  fi
  
  # Check for completion
  if grep -q "Enrichissement complété\|✅.*Enrichissement" /tmp/backend_enrichment.log; then
    echo ""
    echo "✅ ENRICHISSEMENT TERMINÉ!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show summary
    echo ""
    echo "📋 RÉSUMÉ FINAL:"
    grep "✅.*descriptions\|✅.*images\|❌.*Erreurs" /tmp/backend_enrichment.log | tail -5
    break
  fi
  
  sleep 40
done
