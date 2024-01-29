#!/usr/bin/env perl

use strict;
use warnings;
use File::Basename;
use v5.26;

my $hanaBackupFile = shift || die "Syntax Error: $0 <backup_file>\n";
my $hdbBackupCheck = (</usr/sap/[A-Z][A-Z0-9][A-Z0-9]/HDB[0-9][0-9]/exe/hdbbackupcheck>)[0] || die "Error: 'hdbbackupcheck' not found.\n";
my $hdbsql = (</usr/sap/[A-Z][A-Z0-9][A-Z0-9]/HDB[0-9][0-9]/exe/hdbsql>)[0] || die "Error: 'hdbsql' not found.\n";

if (not -f $hanaBackupFile) {die "Error: Backup file '$hanaBackupFile' not found.\n"};
if ($hdbBackupCheck eq '') {die "Error: Program 'hdbbackupcheck' not found.\n"};
if ($hdbsql eq '') {die "Error: Program 'hdbsql' not found.\n"};

$ENV{LD_LIBRARY_PATH} = dirname($hdbBackupCheck) || die "Error: Unable to determine LD_LIBRARY_PATH.\n";
my @backupInfo = qx($hdbBackupCheck -v $hanaBackupFile 2>&1);

print @backupInfo if $ENV{DEBUG};

if (defined $? and $?) {
    die "Error: Execution of hdbbackupcheck failed: ", $? >> 8, "\n", @backupInfo;
}
if (not @backupInfo) {
    die "Error: Unable to determine HANA Backup information from '$hanaBackupFile'.\n";
}

my $backupId = (grep {s/^\s*backupId\s*:\s*//} @backupInfo)[0]; print $backupId if $ENV{DEBUG};
my $dbName = (grep {s/^\s*DatabaseName\s*:\s*//} @backupInfo)[0]; print $dbName if $ENV{DEBUG};
my $sid = (grep {s/^\s*SID\s*:\s*//} @backupInfo)[0]; print $sid if $ENV{DEBUG};

if ($backupId and $dbName and $sid) {
    chomp($backupId, $dbName, $sid);
    my $cmd = "$hdbsql -U SYSTEM_SYSTEMDB BACKUP CATALOG DELETE for $dbName ALL BEFORE BACKUP_ID $backupId COMPLETE";
    say $cmd if $ENV{DEBUG};
    my @out = qx($cmd 2>&1);

    if (defined $? and $?) {
        die "Error: Execution of hdbsql failed: ", $? >> 8, "\n", @out;
    }
    else {
        say "Success: All backups before backup ID $backupId deleted for $dbName.";
    }
} else {
    die "Error: Unable to determine HANA Backup information from '$hanaBackupFile'.\n";
}
