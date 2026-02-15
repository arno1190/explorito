#!/bin/bash
set -euo pipefail

# Explorito database backup script
# Usage: ./scripts/backup.sh [--upload]
# Requires: POSTGRES_USER, POSTGRES_DB env vars (or defaults)

BACKUP_DIR="${BACKUP_DIR:-/opt/explorito/backups}"
POSTGRES_USER="${POSTGRES_USER:-explorito}"
POSTGRES_DB="${POSTGRES_DB:-explorito}"
KEEP_DAYS="${KEEP_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/explorito_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "=== Backing up Explorito database ==="

# Dump and compress
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"

echo "Backup saved: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Clean old backups
find "$BACKUP_DIR" -name "explorito_*.sql.gz" -mtime +"$KEEP_DAYS" -delete
echo "Cleaned backups older than $KEEP_DAYS days"

# Upload to Scaleway Object Storage (optional)
if [ "${1:-}" = "--upload" ]; then
  if command -v s3cmd &> /dev/null; then
    S3_BUCKET="${S3_BUCKET:-s3://explorito-backups}"
    s3cmd put "$BACKUP_FILE" "$S3_BUCKET/"
    echo "Uploaded to $S3_BUCKET"
  else
    echo "s3cmd not found - skipping upload"
  fi
fi

echo "=== Backup complete ==="
