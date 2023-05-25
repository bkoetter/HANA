#!/usr/bin/env perl

use strict;
use warnings;
use 5.018_000;
use List::Util qw(first);
use File::Basename qw(fileparse);

exit main();

sub main {
    my $sid = getSid();
    my $host = getHost();
    my $hdbclnt = getHdbclnt($sid);
    my $hdbinst = getHdbinst();
    my $options = "--batch --check_files --hostname=$host --path=$hdbclnt --sid=$sid";
    system("$hdbinst $options") == 0 or die "Error executing command: '$hdbinst $options': $?\n";
}

sub getSid {
    if (!defined $ENV{SAPSYSTEMNAME}) {
        die "Error: \$SAPSYSTEMNAME not set.\n"
    }
    if ($ENV{SAPSYSTEMNAME} !~ /^[A-Z][A-Z0-9]{2}$/) {
        die "Error: \$SAPSYSTEMNAME invalid: $ENV{SAPSYSTEMNAME}\n"
    }
    return $ENV{SAPSYSTEMNAME};
}

sub getHdbclnt {
    my $sid = shift;
    my $hdbClnt = "/usr/sap/$sid/hdbclient";
    if (!-x $hdbClnt) {
        die "Error: $hdbClnt not found or not executable.\n";
    }
    return $hdbClnt;
}

sub getHost {
    my $host = List::Util::first {s/^DATA FILE\s+:\s.+\/(\w+)\/SSFS_HDB.DAT$/$1/s} qx(hdbuserstore list);
    if (!defined $host) {
        die "Error: Failed to determine host from 'hdbuserstore list'\n";
    }
    chomp $host;
    return $host;
}

sub getHdbinst {
    my @paths = (
        "/catalog/02-extracted/sap-hana-database/SAP_HANA_CLIENT/hdbinst",
        "/opt/sap_media/SAP_HANA/SAP_HANA_CLIENT/hdbinst",
        "/usr/sap/shared/SAP/HANA/SAP_HANA_CLIENT/hdbinst",
    );
    for my $hdbinst (@paths) {
        if (-x $hdbinst) {
            return $hdbinst;
        }
    }
    die "Error: No valid hdbinst found\n";
}