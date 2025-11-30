#!/usr/bin/env bash
set -euo pipefail

NEO4J_HOST="${NEO4J_HOST:-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-NEO4J_PASS}"

echo "Running Neo4j migrations against ${NEO4J_HOST} as ${NEO4J_USER}"

# Apply all .cypher files in lexical order
for f in /migrations/*.cypher; do
  if [ -f "$f" ]; then
    echo "Applying migration: $f"
    cypher-shell \
      -a "bolt://${NEO4J_HOST}:7687" \
      -u "${NEO4J_USER}" \
      -p "${NEO4J_PASSWORD}" \
      -f "$f"
  fi
done

echo "All Neo4j migrations applied."
