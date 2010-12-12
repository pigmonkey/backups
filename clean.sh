#!/usr/bin/env bash

BACKUP_DIR="$HOME/backup"

/usr/bin/find $BACKUP_DIR -type f -mtime +60 -exec /bin/rm -v {} \;
