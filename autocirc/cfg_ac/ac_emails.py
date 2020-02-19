###############
# CONTSTANTS  #
###############
#
# constants that can/should be changed
#
# FOR DEBBUGGING, set overideEmail to an email address. all emails, including patron noticies will go to this address.
# WHEN NOT DEBUGGING, set overideEmail to ""
#overideEmail                    = "bruce.orcutt@utsa.edu"                 # if set, send to this address, rather than the read email address
overideEmail 				    = ""                                       # overideEmail, if not used *******MUST******** EXPLICITLY be set to ""

csvSummaryTo                    = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"  # summary csv report
runSummaryTo                    = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"  # summary of run email, no report
reportsEmail                    = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"  # address to send reports to
printEmail                      = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"	# address to send items that need to be printed and sent via postal mail
illiadEmail                     = "ILL-people@your.edu,A.programmer@your.edu"												   	                # address to send illiad items to
printableFromAddress            = "A-generic-address@your.edu"                																	# Email address to list as from when sending the printable reports
printableRecallTo               = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"	# Email address to send the printable reports to
printableOverduerecallTo        = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"  # Email address to send the printable reports to
printableOverdueTo              = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"
printableCourtesyTo             = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"
printableFinesFeesTo            = "circulation-generic-address@your.edu,manager-drone@your.edu,Access.Services@your.edu,A.programmer@your.edu"

# replaces the LIBNUM text in email notices
libraryNumbers = "X Front Desk  - 210-555-5555\n\t\tY Front Desk  - 123-456-7890"
