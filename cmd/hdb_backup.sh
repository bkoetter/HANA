#!/usr/bin/env bash

if [ X"$1" = "Xweekly" ]; then
    comment="Weekly Backup"
    prefix=$(date +\%F_\%H_\%M)
elif [ X"$1" = "Xmonthly" ]; then
    comment="Monthly Backup"
    prefix="MONTHLY"
else
    echo "Syntax: $0 <weekly|monthly>"
    exit 0
fi

for tenant in SYSTEMDB S4H S4T; do
    if ! sudo -nu ${hdb}adm /catalog/95-automation/scripts/sap/cmd/sap-hana-backup-history-cleanup.pl /hana/shared/$HDB/HDB$db/backup/data/SYSTEMDB/MONTHLY_databackup_0_1; then
        echo "Failed to cleanup backup history for $tenant"
        exit 1
    fi
done

for tenant in SYSTEMDB S4H S4T; do
    echo "Backing up $tenant..."
    sudo -nu ${hdb}adm /usr/sap/$HDB/HDB$db/exe/hdbsql -xU SYSTEM_SYSTEMDB "BACKUP DATA FOR $tenant using FILE ('$prefix') ASYNCHRONOUS COMPRESSED COMMENT '$comment'"
done

sudo -u ${hdb}adm tail -f /usr/sap/$HDB/HDB$db/$HOSTNAME/trace/backup.log /usr/sap/$HDB/HDB$db/$HOSTNAME/trace/DB_$SID/backup.log /usr/sap/$HDB/HDB$db/$HOSTNAME/trace/DB_S4T/backup.log
