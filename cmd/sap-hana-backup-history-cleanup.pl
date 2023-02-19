#!/usr/bin/env perl

use strict;
use warnings;
use File::Basename;
use v5.26;

my $hanaBackupFile = shift || die "Syntax Error: $0 <backup_file>\n";
my $hdbBackupCheck = List::Util::first {-x $_} </usr/sap/[A-Z][A-Z0-9][A-Z0-9]/HDB[0-9][0-9]/exe/hdbbackupcheck>;
my $hdbsql = List::Util::first {-x $_} </usr/sap/[A-Z][A-Z0-9][A-Z0-9]/HDB[0-9][0-9]/exe/hdbsql>;

if (not -f $hanaBackupFile) {die "Error: Backup file '$hanaBackupFile' not found.\n"};
if ($hdbBackupCheck eq '') {die "Error: Program 'hdbbackupcheck' not found.\n"};
if ($hdbsql eq '') {die "Error: Program 'hdbsql' not found.\n"};

$ENV{LD_LIBRARY_PATH} = dirname($hdbBackupCheck) || die "Error: Unable to determine LD_LIBRARY_PATH.\n";
my @backupInfo = qx($hdbBackupCheck -v $hanaBackupFile 2>&1);

if (defined $? and $?) {
    die "Error: Execution of hdbbackupcheck failed: ", $? >> 8, "\n", @backupInfo;
}
elsif (@backupInfo) {
    my $backupId = List::Util::first {s/^\s*backupId\s*:\s*//} @backupInfo;
    my $dbName = List::Util::first {s/^\s*DatabaseName\s*:\s*//} @backupInfo;
    my $sid = List::Util::first {s/^\s*SID\s*:\s*//} @backupInfo;

    if ($backupId and $dbName and $sid) {
        chomp($backupId, $dbName, $sid);
        my @out = qx($hdbsql -U SYSTEM_SYSTEMDB BACKUP CATALOG DELETE for $dbName ALL BEFORE BACKUP_ID $backupId complete 2>&1);

        if (defined $? and $?) {
            die "Error: Execution of hdbsql failed: ", $? >> 8, "\n", @out;
        }
        else {
            say "Success: All backups before backup ID $backupId deleted.";
        }
    }
}
else {
    die "Error: Unable to determine HANA Backup information from '$hanaBackupFile'.\n";
}