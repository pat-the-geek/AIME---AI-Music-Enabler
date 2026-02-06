#!/bin/bash
cd /Users/patrickostertag/Documents/DataForIA/"AIME - AI Music Enabler"/backend
source .venv/bin/activate

# Kill all existing processes
echo "Killing all processes..."
lsof -ti :8000,:3330 2>/dev/null | xargs -r kill -9
sleep 2

# Start backend
echo "Starting backend..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_test.log 2>&1 &
BACKEND_PID=$!
sleep 4

# Start bridge
echo "Starting bridge..."
cd /Users/patrickostertag/Documents/DataForIA/"AIME - AI Music Enabler"/roon-bridge
node app.js > /tmp/bridge_test.log 2>&1 &
BRIDGE_PID=$!
sleep 2

# Run test
echo "Running test..."
cd /Users/patrickostertag/Documents/DataForIA/"AIME - AI Music Enabler"

echo ""
echo "=== TEST 1 ==="
curl -s -X POST 'http://localhost:8000/api/v1/services/roon/normalize/simulate?limit=10' | jq '.status_endpoint'
sleep 1

for i in {1..10}; do
  STATUS=$(curl -s 'http://localhost:8000/api/v1/services/roon/normalize/simulate-results' | jq -r '.status')
  echo "Poll $i: $STATUS"
  if [ "$STATUS" = "completed" ]; then
    echo "✅ TEST 1 COMPLETED"
    break
  fi
  sleep 0.5
done

sleep 2

echo ""
echo "=== TEST 2 ==="
curl -s -X POST 'http://localhost:8000/api/v1/services/roon/normalize/simulate?limit=10' | jq '.status_endpoint'
sleep 1

for i in {1..10}; do
  RESULT=$(curl -s 'http://localhost:8000/api/v1/services/roon/normalize/simulate-results')
  STATUS=$(echo "$RESULT" | jq -r '.status')
  echo "Poll $i: $STATUS"
  if [ "$STATUS" = "completed" ]; then
    echo "✅ TEST 2 COMPLETED"
    break
  elif [ "$STATUS" = "error" ]; then
    ERROR=$(echo "$RESULT" | jq -r '.error')
    echo "❌ TEST 2 ERROR: $ERROR"
    break
  fi
  sleep 0.5
done

# Cleanup
kill $BACKEND_PID $BRIDGE_PID 2>/dev/null
wait

# Show logs
echo ""
echo "=== BACKEND LOGS (last 30 lines with 'simulation') ==="
grep -i "simulation\|run_simulation\|completed\|error" /tmp/backend_test.log | tail -30
