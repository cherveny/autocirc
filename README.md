# autocirc
Automated circulation notices for ExLibris' Voyager ILS.

### License

Please see the `LICENSE` file for details on the license of use.

### Purpose

This program is used for automating the circulation notices from [ExLibris' Voyager](http://www.exlibrisgroup.com/category/Voyager).

Voyager normally requires a client-server program, Reporter, to be run manually, to
generate and email patron circulation notices, and to print notices for those without
email addresses.  This program replaces this process, with a python program, that can be set
to run in `cron` automatically.  This means notices can go out when your library is closed,
no need to tie up staff time, etc.

The program generates these notices from the notices file generated automatically by
the circjobs cronjob.  Thus, this program should run after circjobs is run.

### Requirements

#### Ex Libris Voyager:

It was tested on Voyager 9.1, but should be compatible with most other
versions, although the dictionary parsing may need to trim off a few fields for
earlier versions.

#### Python:
Tested on 2.7, but should work on earlier versions, and should be able
to run on 3+ with only [minor modifications](https://docs.python.org/2/library/2to3.html).

##### Python Libraries:
- csv
- time
- email
- smtplib
- re
- os
- cx_Oracle

### Configuration

Almost all configuration options that would need to be changed are in the
modules within the `cfg_ac` directory.  Be sure to look into and configure each of these files.

#### `ac_doctempl`:
This is used for templates for RTF documents generated when
patrons lack email addresses, but have notices.  For these notices,
postal address information is retrieved from the notices file.

#### `ac_emails`:
This is used for deciding who gets which alerts, such as a
summary of the run, a csv list of the run, a csv list of just ILL related items, RTF files
that are to be printed for patrons that are missing email addresses, etc.

_NOTE_: the `overideEmail` address is special.  If set to any value, it overrides all
email addresses configured in this file, as well as all patron email addresses read from the
notices file.  It is recommended you set this for your first runs to your own email address
to allow for testing before use in full production.  Also, this variable being set also overrides
the normal renaming of the notices file.

#### `ac_emailtmpl`:
Templates used to format the emails sent to patrons.

#### `ac_files`:
File locations.  You'll want to edit at least the notices file location.  To mimic the
function of the Reporter client, after a run, the notices file is renamed to append the  current
day and time.  Also note, if the overideEmail variable is set in ac_emails, this renaming function
is not performed.

#### `ac_misc`:
Remaining variables, such as a read-only database user/password.

### Author:

	Bruce A. Orcutt (@cherveny)
	Senior Systems Analyst
	University of Texas at San Antonio Libraries
	Bruce.Orcutt@utsa.edu


Can't guarantee an immediate response to questions, but will do my best to respond to configuration questions, etc.
