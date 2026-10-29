#!/usr/bin/env bash
# Sauvegarde mensuelle hors serveur : base + fichiers envoyés (avatars, audios)
# vers l'Object Storage Scaleway perso, classe GLACIER (≈ 0,003 €/Go/mois).
#
# Lancé le 1er de chaque mois par /etc/cron.d/explorito-backup (installé par
# prod-build.sh), journal dans /var/log/explorito-backup.log.
# À la main, sur le serveur : bash /opt/explorito/scripts/backup.sh
#
# La clé vit dans /etc/explorito/backup.env (BACKUP_S3_ACCESS_KEY,
# BACKUP_S3_SECRET_KEY), hors de l'arbre que la CI écrase. Elle n'a que le
# droit d'écrire : un serveur compromis ne peut ni lire ni effacer les
# sauvegardes. Le bucket est versionné et efface ce qui a plus de 400 jours.
#
# Restaurer (depuis un poste avec le profil Scaleway perso) :
#   1. aws s3api restore-object --bucket explorito-backups-pascal --key <AAAA-MM…>/explorito.dump \
#        --restore-request Days=2   (Glacier → standard, quelques heures au plus)
#   2. télécharger explorito.dump et uploads.tar.gz, vérifier SHA256SUMS
#   3. pg_restore --clean --if-exists -U explorito -d explorito < explorito.dump
#      tar -C /app/uploads -xzf uploads.tar.gz   (dans le conteneur backend)
set -euo pipefail

cd /opt/explorito
COMPOSE="docker compose -f docker-compose.prod.yml"
BUCKET="${BACKUP_BUCKET:-explorito-backups-pascal}"
LOCAL_DIR=/opt/explorito/backups
KEEP_LOCAL=3
STAMP=$(date -u +%Y-%m-%dT%H%MZ)
DIR="$LOCAL_DIR/$STAMP"

set -a
# shellcheck source=/dev/null
. /etc/explorito/backup.env
set +a

echo "=== $STAMP sauvegarde Explorito ==="
mkdir -p "$DIR"

$COMPOSE exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > "$DIR/explorito.dump"
# Une archive illisible ne doit jamais partir comme « la sauvegarde du mois ».
$COMPOSE exec -T postgres pg_restore --list < "$DIR/explorito.dump" > /dev/null

$COMPOSE exec -T backend tar -C /app/uploads -czf - . > "$DIR/uploads.tar.gz"
tar -tzf "$DIR/uploads.tar.gz" > /dev/null

(cd "$DIR" && sha256sum explorito.dump uploads.tar.gz > SHA256SUMS)
du -sh "$DIR"/*

# Clé passée par l'environnement, jamais sur la ligne de commande (visible
# dans ps). Écriture seule : ni HEAD ni listing, d'où les --no-* ci-dessous.
export RCLONE_CONFIG_SCW_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY"
export RCLONE_CONFIG_SCW_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_KEY"
docker run --rm -v "$DIR":/data:ro \
  -e RCLONE_CONFIG_SCW_TYPE=s3 \
  -e RCLONE_CONFIG_SCW_PROVIDER=Scaleway \
  -e RCLONE_CONFIG_SCW_REGION=fr-par \
  -e RCLONE_CONFIG_SCW_ENDPOINT=s3.fr-par.scw.cloud \
  -e RCLONE_CONFIG_SCW_STORAGE_CLASS=GLACIER \
  -e RCLONE_CONFIG_SCW_ACCESS_KEY_ID -e RCLONE_CONFIG_SCW_SECRET_ACCESS_KEY \
  rclone/rclone:1.68.2 copy /data "scw:$BUCKET/$STAMP" \
  --s3-no-check-bucket --s3-no-head --no-check-dest --no-traverse

# Copies locales : les 3 dernières, pour une restauration rapide sans Glacier.
find "$LOCAL_DIR" -mindepth 1 -maxdepth 1 -type d | sort | head -n -"$KEEP_LOCAL" | xargs -r rm -rf

echo "=== $STAMP envoyée dans $BUCKET (GLACIER) ==="
