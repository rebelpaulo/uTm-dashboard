#!/bin/bash
# Export Antfarm data to JSON and push to GitHub

cd /root/.openclaw/workspace/dashboard-vendas

# Get workflow runs
RUNS=$(antfarm workflow runs --json 2>/dev/null || echo "[]")

# Get workflow list
WORKFLOWS=$(antfarm workflow list --json 2>/dev/null || echo "[]")

# Create JSON with timestamp
cat > antfarm-data.json << EOF
{
  "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "workflows": $WORKFLOWS,
  "runs": $RUNS,
  "status": "active"
}
EOF

# Commit and push
git add antfarm-data.json
git commit -m "Update Antfarm data: $(date -u +"%Y-%m-%d %H:%M UTC")" || echo "No changes"
git push origin master

echo "✅ Antfarm data exported and pushed"
