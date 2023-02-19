#!/usr/bin/env perl

################################################################################
# Author: BK87
# eMail:  infosys.kotter@extaccount.com
# Initial Version: 2018-09-24
# Description: Simple SAP HANA Update Script
################################################################################
# Open issues:
# - Tested on SAP HANA 2.0 only

use strict;
use warnings;
use 5.018_000;
use Pod::Usage qw(pod2usage);
use Getopt::Std;
use Getopt::Long;
use FindBin qw($Bin);
use Net::Domain qw(hostfqdn);
use List::Util qw(first);
our $VERSION = 1.000;

exit main();                                                            # Start program execution and exit with return code

sub main {                                                              # Main program: All functions started from within this block
    my $opts = {};                                                      # Store all command line arguments in a hash
    getopts('c:hd:t:u:vf', $opts);                                      # Define possible command line arguments

    pod2usage(-exitstatus => 0, -verbose => 2) if $opts->{h}||!%$opts;  # Display usage info when called with -h or no arguments
    
    checkEnvironment($opts);                                            # Verify current environment, user, settings
    setHanaUpdateType($opts);                                           # Determine and set HANA Server or COCKPIT
    execSapHanaUpdate($opts);                                           # Execute SAP HANA update command

    return 0;
}

sub checkEnvironment {
    my $opts = shift;

    if (lc($ENV{SAPSYSTEMNAME})."adm" ne getpwuid($>)) {                # Verify valid user (<sid>adm)
        die "$0 must be executed as <sid>adm\n" if !$opts->{f};         # Exit if user other than <sid>adm
    }

    if (not defined $opts->{d}) { die "Option -p <path> must be given.\n" }
    if (not -d      $opts->{d}) { die "Path $opts->{d} does not exist.\n" }

    return 0;
}

sub setHanaUpdateType {
    my $opts = shift;

    if (not defined $opts->{t}) {                                       # If option -t not specified get cockpit from directory
        if ($opts->{d} =~ m/cockpit/i) {                                # If string "cockpit" found in path set type to cockpit
            $opts->{t} = 'cockpit';
        }
        else {                                                          # Default is type is server
            $opts->{t} = 'server';
        }
    }

    return 0;
}

sub execSapHanaUpdate {
    my $opts   = shift;
    $opts->{c} = $opts->{c} || "server,client";
    $opts->{u} = $opts->{u} || "SYSTEM";

    my $xml = (getpwnam(lc($ENV{SAPSYSTEMNAME})."adm"))[7]."/.config/hdb/.secret.xml";
    if (!-f $xml) {
        die "Error: xml-file '$xml' does not exist\n";
    }
    my $cmd = do {
        if ($opts->{t} eq "cockpit") {
            my $hdblcm = getHdblcmExe("$opts->{d}/hdblcm.sh");
            "cat $xml | $hdblcm --action=update --batch --component_root=$opts->{d} --sid=$ENV{SAPSYSTEMNAME} --system_user=$opts->{u} --verify_signature --read_password_from_stdin=xml -components=all --org_manager_user=COCKPIT_ADMIN --remote_execution=saphostagent";
        }
        else {
            my $hdblcm = getHdblcmExe("$opts->{d}/SAP_HANA_DATABASE/hdblcm");
            "cat $xml | $hdblcm --action=update --batch --component_root=$opts->{d} --sid=$ENV{SAPSYSTEMNAME} --system_user=$opts->{u} --verify_signature --read_password_from_stdin=xml --components=all";
        }
    };

    say $cmd;
    system($cmd);
    if (defined $? && $ != 0) {
        say "STATUS: WARNING: Execution ended with non-zero error code: $?";
    }
    else {
        say "STATUS: OK"
    }

    return 0;
}

sub getHdblcmExe {
    my $file = shift;

    if (!-x $file) {
        die "Error: file $file not found or not executable.\n";
    }
    else {
        return $file;
    }
}

__END__

=head1 NAME

    updateSapHana.pl - Execute SAP HANA Update

=head1 SYNOPSIS

    updateSapHana.pl [-hv][-u <user>][-c <component list>][-t server|cockpit] -d <dir>

=head1 OPTIONS

=over 4

     Options:
       -h           Provide help message
       -d <dir>     Provide location of extracted update componentes (component_root)
       -u <user>    Provide user for SystemDB (optional; default=SYSTEM)
       -c <comp>    Provide component list, "server,client" (optional; default=all)
       -t <type>    Optional: SAP HANA update type: server or cockpit
       -f           Force mode to update as root user
       -v           Enable verbose mode

Program gathers information from curent environment and compiles command to update SAP HANA.
Must be executed as <sid>adm

Only updates server and client components.

=back

=head1 DESCRIPTION

In some cases the update might not complete when exeucted as <sid>adm. In such cases execute the same command again as root user.

=cut
