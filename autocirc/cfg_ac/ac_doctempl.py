#constants that probably won't change much
#
#
# FYI, RTF standard at http://www.biblioscape.com/rtf15_spec.htm#Heading6

# standard RTF header, set text to ANSI, define font as courier
# note, certain \ characters need \\ as python tries to interpret as control chars.
rtfHeader               = "{\\rtf1\\ansi\deff0 {\\fonttbl {\\f0 Times New Roman;}}"

# Overdue notices for those with no email, cover page
rtfNoEmailOverdueCover  = '''
\par\pard
\qc
\\vertalc
\\fs50
Printable Pages For Patrons Without Email Addresses\line\line
Overdue Notices\line \line

[{!CURRDATE!}] \line

\page
\par
\\vertalt
\ql
\\fs20


'''

rtfNoEmailRecallCover  = '''
\par\pard
\qc
\\vertalc
\\fs50
Printable Pages For Patrons Without Email Addresses\line\line
Recall Notices\line \line

[{!CURRDATE!}] \line

\page
\par
\\vertalt
\ql
\\fs20


'''

rtfNoEmailOverduerecallCover  = '''
\par\pard
\qc
\\vertalc
\\fs50
Printable Pages For Patrons Without Email Addresses\line\line
Overdue Recall Notices\line \line

[{!CURRDATE!}] \line

\page
\par
\\vertalt
\ql
\\fs20

'''

rtfNoEmailFinesfeesCover  = '''
\par\pard
\qc
\\vertalc
\\fs50
Printable Pages For Patrons Without Email Addresses\line\line
Fines & Fees Notices\line \line

[{!CURRDATE!}] \line

\page
\par
\\vertalt
\ql
\\fs20

'''

rtfSummaryFinesfeesCover  = '''
\par\pard
\qc
\\vertalc
\\fs50
Summary Report of Patrons With Excessive Fines\line\line

[{!CURRDATE!}] \line

\page
\par
\\vertalt
\ql
\\fs20

'''

rtfNoEmailCourtesyCover  = '''
\par\pard
\qc
\\vertalc
\\fs50
Printable Pages For Patrons Without Email Addresses\line\line
Courtesy Notices\line \line

[{!CURRDATE!}] \line

\page
\par
\\vertalt
\ql
\\fs20

'''
