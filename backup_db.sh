#!/bin/bash

# Setup variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_PATH="/home/connormunger/tcg-app/tcg.db"
BACKUP_DIR="/tmp/tcg_backups"
BUCKET_NAME="gs://riftbound-db-backups"

# Create a temporary local folder
mkdir -p $BACKUP_DIR

# Clone the live database
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/tcg_$TIMESTAMP.db'"

# Compress the clone to save space
gzip "$BACKUP_DIR/tcg_$TIMESTAMP.db"

# Upload the compressed file directly to bucket
gcloud storage cp "$BACKUP_DIR/tcg_$TIMESTAMP.db.gz" $BUCKET_NAME/

# Clean up the temporary local file
rm -rf $BACKUP_DIR
