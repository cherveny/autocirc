#!/usr/local/bin/python
import csv
import time
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import encoders
import smtplib
import re				# regular expressions
import os				# filename rename after runs
import cx_Oracle
from cfg_ac import *	# loads all config files (setting filenames, email addresses, etc)



######################
# autocircucat
# By: Bruce A. Orcutt
# 7/2016
# takes circulation noticies file from circjob
# parses the file into dicts of noticies to process
# sends emails to patrons with email addresses on file
# collects notices for patrons sans email addresses into RTFs
# RTF documents emailed to access services staff, to allow for manual printing and mailing of notices
# summary of ILL items in overdue, recall etc status compiled and sent to ILL staff
# summary of entire run sent to access services staff
#s
# Modifications
# 04jan2017 epc add /mi/incoming (to commented out vbin access)
# 1/4/2017 Per TKT-183, added findSSAN, which calls oracle, to get banner IDs



##############
# GLOBALS    #
##############

# summary csv file of all alerts
csvSummaryString                = ""

# flags if one or more patrons lack email addresses and require alerts to be printed
printableDoc2OverdueFlag       = 0
printableDoc3RecallFlag        = 0
printableDoc4OverduerecallFlag = 0
printableDoc5FinesFeesFlag     = 0
printableDoc7CourtesyFlag      = 0
summaryDoc5FinesFeesFlag       = 0

# regular expression used to verify valid email address pattern
emailPattern = re.compile(r"[^@]+@[^@]+\.[^@]+")


##############
# FUNCTIONS  #
##############
########### Database query functions

def findSSAN(patronID):
	# function to get a users SSAN (bannerID) based on patronID
	# returns String NONE if value is None (alumni users, etc)
	# added to allow for banner id to go in summary, as per TKT-193

	ssan = "NONE";

	# make connection to the database
	dsn = cx_Oracle.makedsn("localhost","1521","VGER")
	con = cx_Oracle.connect(user=db_user,password=db_password,dsn=dsn)
	cur = con.cursor()

	# run the query
	query = """
		SELECT
		    pt.ssan
		FROM
		    patron pt
		WHERE
		    pt.patron_id IN ({pID})
	"""
	cur.execute(query.format(pID=patronID));

	try:
		ssan	= cur.fetchone()[0]
	except:
		ssan = "NONE"


	if ssan == None:
		ssan = "NONE"
	else:
		ssan = "@" + ssan[1:]

	return ssan;


def findItemType(barCode):
	# function to get the type of an item, based on itemId.
	# checks for temporary item ID being set, if so, returns that type instead
	# Note: dicts field itemId isn't really itemId, it's item barcode
	# dict's barcode field is PATRON barcode
	itemType = "NONE";

	# make connection to the database
	dsn = cx_Oracle.makedsn("localhost","1521","VGER")
	con = cx_Oracle.connect(user=db_user,password=db_password,dsn=dsn)
	cur = con.cursor()

	# run the query
	query = """
		SELECT
			itt.item_type_name
		FROM
			item it,
			item_type itt,
			item_barcode ib
		WHERE
			ib.item_barcode IN ('{itemNumber}') AND
			ib.item_id = it.item_id AND
			itt.item_type_id = CASE WHEN (it.temp_item_type_id = '0') THEN it.item_type_id ELSE it.temp_item_type_id END
	"""

	cur.execute(query.format(itemNumber=barCode));

	try:
		itemType	= cur.fetchone()[0]
	except:
		itemType = "NONE"

	if itemType == None:
		itemType = "NONE"

	return itemType;

##########Utility Functions
def printthedict(L):
	# utility function for debugging
	for dicts in L:
		print "-=-=-=-=-=-"
		for key in dicts:
			print key, " \t = \t ",dicts[key]

def errorLogger(severity,textToLog):
	# allow logging of our errors, usually called in except blocks
	print severity,": ",textToLog
	f = open(errorLog,"ab")
	f.write(time.ctime() + severity +  ": " + textToLog + "\n")
	f.close()

##########Report and Email Functions

def summaryForManagers():
	# prepare a summary email, giving statistics of today's run
	stringToSend = ""

	# print for now, later will email.
	print "Overdue Notifications"
	print "Overdue items:                           ",overdueCount["itemCount"]
	print "People with Overdue Items:               ",overdueCount["personCount"]
	print "Overdue notices lacking email:           ",overdueCount["noEmailCount"]
	print "ILL items Overdue:                       ",overdueCount["ill"]
	print "ILL items recalled:                      ",recallCount["ill"]
	print "Recall notifications:                    ",recallCount["itemCount"]
	print "People with Recalled items:              ",recallCount["itemCount"]
	print "Recall notices lacking email:            ",recallCount["noEmailCount"]
	print "ILL items overdue on recall:             ",overdueRecallCount["itemCount"]
	print "Recall Overdue notifications:            ",overdueRecallCount["itemCount"]
	print "People with Overdue Recalled items:      ",overdueRecallCount["personCount"]
	print "Recall notices lacking email:            ",overdueRecallCount["noEmailCount"]
	print "Courtesy notifications:                  ",courtesyCount["itemCount"]
	print "People with Courtesy notes:              ",courtesyCount["personCount"]
	print "Courtesy notices lacking email:          ",courtesyCount["noEmailCount"]
	print "Fine/Fee notifications:                  ",finesFeesCount["itemCount"]
	print "People with Fine/Fee notes:              ",finesFeesCount["personCount"]
	print "Fine/Fee notices lacking email:          ",finesFeesCount["noEmailCount"]
	print "Fines/Fees above limit:                  ",finesFeesCount["ill"]

	stringToSend =  "Overview of Circulation Notices Run:\n" +                                      \
                        "====================================\n" +                                      \
                        "OVERDUE"                                   + "\n" + \
                        "-------"                               	+ "\n" + \
                        "Overdue Items\t\t\t\t\t"                   + `overdueCount["itemCount"]`    	+	"\n" + \
                        "People with Overdue Items:\t\t\t"          + `overdueCount["personCount"]`	 	+	"\n" + \
                        "Overdue notices lacking email:\t\t\t"      + `overdueCount["noEmailCount"]` 	+	"\n" + \
                        "ILL items Overdue:\t\t\t\t"   		   + `overdueCount["ill"]`          	+  "\n" + \
                        "\n" 								   	    + \
                        "RECALL"                                	+ "\n" + \
                        "-------"                                   + "\n" + \
                        "ILL items recalled:\t\t\t\t"               + `recallCount["ill"]`           	+  "\n" + \
                        "Recall notifications:\t\t\t\t"             + `recallCount["itemCount"]`     	+  "\n" + \
                        "People with Recalled items:\t\t\t"         + `recallCount["personCount"]`   	+  "\n" + \
                        "Recall notices lacking email:\t\t\t"       + `recallCount["noEmailCount"]`  	+  "\n" + \
                        "\n" 								    	+ \
                        "RECALLS OVERDUE"                           + "\n" + \
                        "---------------"                           + "\n" + \
                        "ILL items overdue on recall:\t\t\t"        + `overdueRecallCount["ill"]`	 		+  "\n" + \
                        "Recall Overdue notifications:\t\t\t"       + `overdueRecallCount["itemCount"]` 	+  "\n" + \
                        "People with Overdue Recalled items:\t\t"   + `overdueRecallCount["personCount"]`   +  "\n" + \
                        "Overdue recall notices lacking email:\t\t" + `overdueRecallCount["noEmailCount"]`  +  "\n" + \
                        "\n" 								   	    + \
                        "COURTESY"                                  + "\n" + \
                        "-------"                                   + "\n" + \
                        "Courtesy notifications:\t\t\t\t"           + `courtesyCount["itemCount"]`	  +  "\n" + \
                        "People with Courtesy notes:\t\t\t"         + `courtesyCount["personCount"]`  +	 "\n" + \
                        "Courtesy notices lacking email:\t\t\t"     + `courtesyCount["noEmailCount"]` +	 "\n" + \
                        "\n" 								   		+ \
                        "FINES/FEES"                                + "\n" + \
                        "-------"                                   + "\n" + \
                        "Fine/Fee notifications:\t\t\t\t"           + `finesFeesCount["itemCount"]`            +  "\n" + \
                        "People with Fine/Fee notes:\t\t\t"         + `finesFeesCount["personCount"]`          +  "\n" + \
                        "Fine/Fee notices lacking email:\t\t\t"     + `finesFeesCount["noEmailCount"]` +	"\n"

	try:
		sendEmail(stringToSend,runSummaryTo,"Summary of Circulation Notices Run")
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error sending manager text summary")



def sendEmail(textToSend,emailToSendTo,subject):
	#Function to allow sending of emails, sans attachments

	global overideEmail

	# overideEmail is a debug email to prevent real email addresses from being used, and use this one instead, for testing
	if overideEmail:
		sendEmailAddr = overideEmail
	else:
		sendEmailAddr = emailToSendTo

	try:
			msg             = MIMEMultipart()
			msg['From']     = printableFromAddress
			msg['To']       = sendEmailAddr
			msg['Subject']  = subject

			msg.attach(MIMEText(textToSend,'plain'))

			server = smtplib.SMTP(emailServer, 25)
			#server.starttls()
			text = msg.as_string()
			server.sendmail(printableFromAddress, sendEmailAddr.split(","), text)
			server.quit
	except Exception, e:
     		errorLogger("MAJOR",repr(e) + "sendEmail() " + printableFromAddress + " " + sendEmailAddr + " " + text )



def sendEmailPrintable(textToSend,fileToSend,addressToSend, pathToFile, subject):
	# email function for sending attachments

	global overideEmail

	# overideEmail is a debug email to prevent real email addresses from being used, and use this one instead, for testing
	if overideEmail:
		sendEmailAddr = overideEmail
	else:
		sendEmailAddr = addressToSend

	text = ''
	msg             = MIMEMultipart()
	msg['From']     = printableFromAddress
	msg['To']       = sendEmailAddr
	msg['Subject']  = subject

	try:
		msg.attach(MIMEText(textToSend,'plain'))
		attachment = open(pathToFile+fileToSend, "rb")
		part       = MIMEBase('application','octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % fileToSend)

		msg.attach(part)

		server = smtplib.SMTP(emailServer, 25)
		#server.starttls()
		text = msg.as_string()
		server.sendmail(printableFromAddress, sendEmailAddr.split(","), text)
		server.quit
		attachment.close()

	except Exception, e:
		print repr(e)
		errorLogger("MAJOR", repr(e) + "error sendng printable postal document with subject" + subject)

##############CSV Functions
def csv_header(Header,fileName):
	try:
		fileHandle = open(fileName, 'wb')
		csvWriter  = csv.writer(fileHandle,dialect='excel')
		csvWriter.writerow(Header)
		fileHandle.close()
	except:
		print repr(e)
		errorLogger("SEVERE", repr(e) + "error opening csv file to write header " + fileName)

def addToIllCsv(fileName,noticeDict):
	csvFile 	= open(fileName,'ab')
	csvWriter	= csv.writer(csvFile,dialect='excel')

	try:
		csvWriter.writerow(["'" + 	noticeDict["ItemId"],
									noticeDict["ItemCall"],
									noticeDict["DueDate"],
									noticeDict["ItemTitle"],
									noticeDict["ItemAuthor"],
							])
		csvFile.close()
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error adding item to ILL csv Overdue, item id is " + str(noticeDict) )

def addToSummaryCsv(fileName,noticeDict,noticeType):
# Add item to summary csv
	try:
		ssan		= "NONE"	# patron's institutional ID
		itemType	= "NONE"	# item type of item related to notice

		# These two items require querying the database
		# as not included within the notices file
		ssan 	 = findSSAN(noticeDict["PatronId"])
		itemType = findItemType(noticeDict["ItemId"])

		# add the item to the CSV
		csvFile	  = open(fileName, 'ab')
		csvWriter = csv.writer(csvFile,dialect='excel')
		csvWriter.writerow([noticeType,
	              			noticeDict["Library"],
	                        "'" + noticeDict["ItemId"],
							itemType,
	                        noticeDict["ItemCall"],
	                        noticeDict["LastName"],
	                        noticeDict["FirstName"],
							ssan,
	                        noticeDict["ItemTitle"],
	                        noticeDict["ItemAuthor"],
	                        "0.0"
	 					])
		csvFile.close()
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error writing line to summary  CSV, Line is " + str(noticeDict))

#######Email Functions
def buildEmailIntro(noticeDict,patronText):
	# build the email to send
	# add intro before calling
	# if ILLFirst name don't even call (illiadFlag)

	# start with the text we got
	returnText = patronText

	# replace the variable positions with date, patron name, library name
	returnText = returnText.replace("[{!DATE!}]",time.strftime("%x").lstrip(" "))
	returnText = returnText.replace("[{!INSTNAME!}]",noticeDict["InstitutionName"].lstrip(" "))
	returnText = returnText.replace("[{!FNAME!}]",noticeDict["FirstName"].lstrip(" "))
	returnText = returnText.replace("[{!LNAME!}]",noticeDict["LastName"].lstrip(" "))

	# check for if we have a valid email address
	if  not noticeDict["Email"] or not emailPattern.match(noticeDict["Email"]):
		# If no email address, or invalid format, give Postal address, if present
		tempAddr = ""
		addrIndex = 1
		#overdueCount["noEmailCount"] += 1

		# check for a title, use it if it exists
		if noticeDict["PatronTitle"]:
			tempAddr  = noticeDict["PatronTitle"] + " "
		tempAddr += noticeDict["FirstName"] + " "
		tempAddr += noticeDict["LastName"] + " \n"

		# Address has 5 parts, but only want to print parts that exist for this patron
		for addrIndex in range(1, 5):
			if noticeDict["Addr" + str(addrIndex)]:
				tempAddr += noticeDict["Addr" + str(addrIndex)] + " \n"
		tempAddr += noticeDict["City"] + ", "
		tempAddr += noticeDict["State"] + " "
		tempAddr += noticeDict["PostalCode"] + " \n"
		returnText = returnText.replace("[{!POSTAL!}]",tempAddr)

	else:
		# No need for postal address if an email
		returnText = returnText.replace("[{!POSTAL!}]","")

	return returnText

def addEmailItem(noticeDict,patronText):
	# add item info to email text

	try:
		returnText = patronText

		# fill in the first items details
		returnText = returnText.replace("[{!LOC!}]",   noticeDict["Library"].lstrip(" "))
		returnText = returnText.replace("[{!NOT!}]",   noticeDict["Sequence"].lstrip(" "))
		returnText = returnText.replace("[{!TITLE!}]", noticeDict["ItemTitle"].lstrip(" "))
		returnText = returnText.replace("[{!AUTHOR!}]",noticeDict["ItemAuthor"].lstrip(" "))
		returnText = returnText.replace("[{!ITEMID!}]",noticeDict["ItemId"].lstrip(" "))
		returnText = returnText.replace("[{!CALL!}]",  noticeDict["ItemCall"].lstrip(" "))
		returnText = returnText.replace("[{!DUE!}]",   noticeDict["DueDate"].lstrip(" "))

		return returnText

	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error adding item info to email text , Notice is " + str(noticeDict))

def addFineEmail(noticeDict, tempText):
	returnText = tempText

	try:
		# fines and fees takes additional items
		returnText = returnText.replace("[{!LOC!}]",   noticeDict["Library"].lstrip(" "))
		returnText = returnText.replace("[{!TITLE!}]", noticeDict["ItemTitle"].lstrip(" "))
		returnText = returnText.replace("[{!AUTHOR!}]",noticeDict["ItemAuthor"].lstrip(" "))
		returnText = returnText.replace("[{!ITEMID!}]",noticeDict["ItemId"].lstrip(" "))
		returnText = returnText.replace("[{!CALL!}]",  noticeDict["ItemCall"].lstrip(" "))
		returnText = returnText.replace("[{!DUE!}]",   noticeDict["MysteryDate2"].lstrip(" "))
		returnText = returnText.replace("[{!DDWF!}]",  noticeDict["FineFeeDate"].lstrip(" "))
		returnText = returnText.replace("[{!CDATE!}]", noticeDict["CurrentDate"].lstrip(" "))
		returnText = returnText.replace("[{!DESC!}]",  noticeDict["FineFeeDescription"].lstrip(" "))
		returnText = returnText.replace("[{!FFA!}]",   noticeDict["FineFeeAmount"].lstrip(" "))
		returnText = returnText.replace("[{!FFB!}]",   noticeDict["FineFeeBalance"].lstrip(" "))
		returnText = returnText.replace("[{!PB!}]",    noticeDict["PreviouslyBilled"].lstrip(" "))
		returnText = returnText.replace("[{!TFF!}]",   noticeDict["TotalFinesFees"].lstrip(" "))
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error adding fine/fee specific details to email item, notice is  : " + str(noticeDict))

	return returnText

##################################################
##################################################
# MAIN BLOCK START ###############################
##################################################
##################################################

#############
# CSV FILES #
#############
# Start CSV files for summary for circulation/access services and ILL owned items for ILL team

# summary CSV file

# Summary file CSV header
csvHeader = ["TYPE","LOCATION","BARCODE","ITEM TYPE","CALL#","LAST","FIRST","BANNER","TITLE","AUTHOR","FINE"]
csv_header(csvHeader,tmpLocation + csvFile)
# CSV file to be sent to ILL people.
csvHeader = ["Barcode","Call #","Due Date","Title", "Author"]
csv_header(csvHeader,tmpLocation + overdueIlliadFile)
csvHeader = ["Barcode","Call #","Due Date","Title", "Author"]
csv_header(csvHeader,tmpLocation + recallIlliadFile)
csvHeader  = ["Barcode","Call #","Due Date","Title", "Author"]
csv_header(csvHeader,tmpLocation + overdueRecallIlliadFile)

####################
# PREPARSING SETUP #
####################

# base contains field names for base of all notices
circbase = (
		"NoticeId",
		"VersionNumber",
		"Email",
		"PatronId",
		"LastName",
		"FirstName",
		"PatronTitle",
		"Addr1",
		"Addr2",
		"Addr3",
		"Addr4",
		"Addr5",
		"City",
		"State",
		"PostalCode",
		"Country",
		"Phone",
		"CurrentDate",
		"InstitutionName",
		"Library",
		"LibAddr1",
		"LibAddr2",
		"LibAddr3",
		"LibCity",
		"LibState",
		"LibPostalCode",
		"LibCountry",
		"LibPhone",
		"ItemTitle",
		"ItemAuthor",
		"ItemId",
		"ItemCall",
		"Enum")

#suffix for type 2, overdue notice
type2suffix = (
		"DueDate",
		"Sequence",
		"ProxyLastName",
		"ProxyFirstName",
		"ProxyTitle",
		"Undocumented")

#suffix for type 3, recall notice
type3suffix = (
		"DueDate",
		"ProxyLastName",
		"ProxyFirstName",
		"ProxyTitle",
		"Undocumented")

#suffix for type 4, recall overdue notice
type4suffix = (
		"DueDate",
		"Sequence",
		"ProxyLastName",
		"ProxyFirstName",
		"ProxyTitle",)

#suffix for type 5, fine fee notice
type5suffix = (
		"FineFeeDate",
		"FineFeeDescription",
		"FineFeeAmount",
		"FineFeeBalance",
		"PreviouslyBilled",
		"TotalFinesFees",
		"MysteryDate",
		"MysteryDate2")

#suffix for type 7, courtesy
type7suffix = (
		"DueDate",
		"ProxyLastName",
		"ProxyFirstName",
		"ProxyTitle")

# set up the delimiter for SIF file format from Voyager
try:
	csv.register_dialect('SIF', delimiter="|")
except Exception, e:
	print repr(e)
	errorLogger("MINOR", repr(e) + "error setting up SIF dialect for input file")


# list of dicts for each type
circ2Overdue            = []
circ3Recall             = []
circ4Overduerecall      = []
circ5Finesfees          = []
circ7Courtesy           = []

# set up the field types
type2OverdueFields          = circbase + type2suffix
type3RecallFields           = circbase + type3suffix
type4OverduerecallFields    = circbase + type4suffix
type5FinesfeesFields        = circbase + type5suffix
type7CourtesyFields         = circbase + type7suffix

# variables populated for management summary
countKeys = ('itemCount','personCount','noEmailCount','ill')

overdueCount 		= dict.fromkeys(countKeys,0)
recallCount  		= dict.fromkeys(countKeys,0)
overdueRecallCount	= dict.fromkeys(countKeys,0)
courtesyCount 		= dict.fromkeys(countKeys,0)
# Note, ill on finesFees is actually
finesFeesCount		= dict.fromkeys(countKeys,0)

# set up the Overdue notices thgat need to be printed document for patrons with no email address
try:
	printableDoc2Overdue        = rtfHeader + rtfNoEmailOverdueCover.replace("[{!CURRDATE!}]",time.strftime("%c"))
	printableDoc3Recall         = rtfHeader + rtfNoEmailRecallCover.replace("[{!CURRDATE!}]",time.strftime("%c"))
	printableDoc4Overduerecall  = rtfHeader + rtfNoEmailOverduerecallCover.replace("[{!CURRDATE!}]",time.strftime("%c"	))
	printableDoc5FinesFees      = rtfHeader + rtfNoEmailFinesfeesCover.replace("[{!CURRDATE!}]",time.strftime("%c"))
	printableDoc7Courtesy       = rtfHeader + rtfNoEmailCourtesyCover.replace("[{!CURRDATE!}]",time.strftime("%c"))
except Exception, e:
	print repr(e)
	errorLogger("MINOR", repr(e) + "error creating rtf document feader/cover page")

# regular expression used to verify valid email address pattern
emailPattern = re.compile(r"[^@]+@[^@]+\.[^@]+")

#csvSummaryString = csvHeader

##############################################
# PARSE THE NOTICES INTO DICTS FOR LATER USE #
##############################################

# open the notices file

try:
	F = open(noticesFile, "r")

	# The notices file is pipe delimited
	csvreader = csv.reader(F, dialect="SIF")

except Exception, e:
	print repr(e)
	errorLogger("CRITICAL", repr(e) + "error seading notices file! : " + noticesFile)

# parse each row of the notices file
for row in csvreader:
	# fields to use for dict vary based on first field
	if not row:
		# do we have a blank row, unparsable, soldier on
		errorLogger("WARNING", "blank row detected from SIF file.  May have garbled line or extra CR/LF")
		continue
	if   row[0] == "02":
		tempfields = type2OverdueFields
	elif row[0] == "03":
		tempfields = type3RecallFields
	elif row[0] == "04":
		tempfields = type4OverduerecallFields
	elif row[0] == "05":
		tempfields = type5FinesfeesFields
	elif row[0] == "07":
		tempfields = type7CourtesyFields
	else:
                # Hope we never get here.
                #### Make this exception
		print "unhandled ",row[0]
		errorLogger("MAJOR", repr(e) + "Error, row type undefined! : " + row[0])
		continue

	# temporary dictionary to fill up and later add to list
	tempdict = dict()

	# for parsing dictionary field names
	index = 0

	# add each item to the dict, reading field names one by one
	#### Add try/exception for not enough fields
	for item in row:
			tempdict[tempfields[index]] = item
			index =  index + 1
	try:
		if not row:
			# do we have a blank row, unparsable, soldier on
			errorLogger("WARNING", "blank row detected from SIF file.  May have garbled line or extra CR/LF")
			continue
		# add the new dict to the proper list
		if   row[0] == "02":
			circ2Overdue.append(tempdict)
		elif row[0] == "03":
			circ3Recall.append(tempdict)
		elif row[0] == "04":
			circ4Overduerecall.append(tempdict)
		elif row[0] == "05":
			circ5Finesfees.append(tempdict)
		elif row[0] == "07":
			circ7Courtesy.append(tempdict)
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "could not put row in dictionary, last name is " + tempdict["LastName"])

F.close()
###################################
# PARSE THE DICTS AND SEND EMAILS #
###################################


# Sort the lists based on the email key of the dictionaries (so can combine email items, if needed)
try:
	circ2Overdue            = sorted(circ2Overdue,       key= lambda k: k['Email'])
	circ3Recall             = sorted(circ3Recall,        key= lambda k: k['Email'])
	circ4Overduerecall      = sorted(circ4Overduerecall, key= lambda k: k['Email'])
	circ5Finesfees          = sorted(circ5Finesfees,     key= lambda k: k['Email'])
	circ7Courtesy           = sorted(circ7Courtesy,      key= lambda k: k['Email'])
except Exception, e:
	print repr(e)
	errorLogger("MINOR", repr(e) + "could not sort list of dicts on email address")


#################
######################
# Parse circ2Overdue #
######################

# used for traversing circ2Overdue list of dicts
index = 0

# build the text of each email
tempText = ""

# Illiad detected flag
illiadFlag = 0

# replacing iterable for look with while loop, so easier to skip when same email address found by increasing index.
while index < len(circ2Overdue):
	index += 1

	# Check for Ill user
	if circ2Overdue[index-1]["FirstName"] == illiadFirst:
		illiadFlag           = 1
		overdueCount["ill"] += 1

		try:
			addToIllCsv(tmpLocation + overdueIlliadFile, circ2Overdue[index-1])
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding item to ILL csv Overdue, notice is " + str(circ2Overdue[index-1]) )

	else:
			overdueCount["personCount"] += 1
			overdueCount["itemCount"]   += 1

	if not illiadFlag:
		# regular item, not ill, so set the header area
		# Make the intro
		try:
			tempText = emailIntroText2Overdue
			tempText = buildEmailIntro(circ2Overdue[index-1],tempText)
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding intro to email text " + str(circ2Overdue[index-1]))

		if not circ2Overdue[index-1]["Email"] or \
			not emailPattern.match(circ2Overdue[index-1]["Email"]):
				# If no email address, or invalid format
				overdueCount["noEmailCount"] += 1

		try:
			# add 2nd part of template
			tempText += emailItemText2Overdue

			# fill in the first items details
			tempText  = addEmailItem(circ2Overdue[index-1],tempText)
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding item to Overdue notice email " + str(circ2Overdue[index-1]))

        # Add item to summary csv
		try:
			addToSummaryCsv(tmpLocation + csvFile,circ2Overdue[index-1],"OVERDUE")
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error writing line to summary 1stOverdue CSV, notice text is " + str(circ2Overdue[index-1]))

        # Is the next item also for the same email address, then fill them out in the same email!
        # ALSO CHECK FIRST NAME, otherwise we lump all no-email people into one!
		while (index < len(circ2Overdue)) and \
			(circ2Overdue[index]["Email"]     == circ2Overdue[index-1]["Email"]) and \
			(circ2Overdue[index]["FirstName"] == circ2Overdue[index-1]["FirstName"]) and \
			(circ2Overdue[index]["LastName"]  == circ2Overdue[index-1]["LastName"]):

			index                   += 1    # move to the next.

			# if it's an ILL item, throw into the ILL CSV
			if illiadFlag:
				try:
					overdue["ill"] += 1
					addToIllCsv(tmpLocation + overdueIlliadFile, circ2Overdue[index-1])
				except Exception, e:
					print repr(e)
					errorLogger("MINOR", repr(e) + "error adding to Overdue ILL CSV File")

			else:
				overdueCount["itemCount"] += 1

				try:
					tempText += emailItemText2Overdue
					tempText  = addEmailItem(circ2Overdue[index-1],tempText)
				except Exception, e:
					errorLogger("MINOR", repr(e) + "error adding to item to email" + str(circ2Overdue[index-1]))

                # Add item to summary csv
				try:
					addToSummaryCsv(tmpLocation + csvFile,circ2Overdue[index-1],"OVERDUE")
				except Exception, e:
					print repr(e)
					errorLogger("MINOR", repr(e) + "error adddng overdue notice to 2ndOverdue summary CSV with notice line" + str(circ2Overdue[index-1]))

        # Lastly, add the standard footer.
        tempText += emailFooterText2Overdue

        tempText = tempText.replace("[{!LIBNUM!}]", "JPL Front Desk  - 210-458-4574\n\t\tDTL Front Desk  - 210-458-2440")

        # Time to check if we have an email address
        if (not circ2Overdue[index-1]["Email"] or not emailPattern.match(circ2Overdue[index-1]["Email"])) \
           and not illiadFlag:
                # first add RTF line breaks
                tt2 = ""
                for line in tempText.splitlines():
                        tt2 += line + "\line\n"
                # print tempText
                printableDoc2Overdue += tt2 + "\line \page"
                printableDoc2OverdueFlag = 1

        elif illiadFlag:
                # ILL not needed
                pass
        else:
                # email text constructed, function to parse email address and send.
			try:
				sendEmail(tempText,circ2Overdue[index-1]["Email"],"Your library item is overdue")
			except Exception, e:
				print repr(e)
				errorLogger("MINOR", repr(e) + "error sendng overdue email with ItemId" + str(circ2Overdue[index-1]))

        # clear illiad flag for next iteration
        illiadFlag = 0

        #######################
        # END OF OVERDUE LOOP #
        #######################

if printableDoc2OverdueFlag:
	# Have overdue notices with no email address to print? Create RTF and send
	printableDoc2Overdue += "}" # close the RTF if we made one
	try:
		f = open(tmpLocation + printableOverdueFile,"wb")
		f.write(printableDoc2Overdue)
		f.close()
		sendEmailPrintable("Overdue notices requiring manual printing",printableOverdueFile, printableOverdueTo, tmpLocation,"Overdue notices requiring manual printing")
	except Exception, e:
		print repr(e)
		errorLogger("MAJOR", repr(e) + "Error sending printable overdue file")

if overdueCount["ill"] > 0:
	try:
		sendEmailPrintable("ILL items Overdue in Voyager",overdueIlliadFile,illiadEmail, tmpLocation, "Overdue ILL Items within Voyager")
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "Error sending overdue ILL file")

        ##################
        # END OF OVERDUE #
        ##################


###########################
# RECALL PROCESSING START #
###########################
######################
# Parse circ3Recall #
######################

# preformated text to use for emails for overdue notices
#[{! brackets are strings to be replaced with .replace
# used for traversing circ3Recall list of dicts
index = 0

# build the text of each email
tempText = ""

# Illiad detected flag
illiadFlag = 0

# replacing iterable for look with while loop, so easier to skip when same email address found by increasing index.
while index < len(circ3Recall):
	index += 1

	# Check for Illiad user
	if circ3Recall[index-1]["FirstName"] == illiadFirst:
		illiadFlag      	  = 1
		recallCount["ill"]   += 1
		try:
			addToIllCsv(tmpLocation + recallIlliadFile,circ3Recall[index-1])
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding item to Recall ILL CSV File")

	else:
		recallCount["personCount"] += 1
		recallCount["itemCount"]   += 1

		# regular item, not illiad, so set the header area
		if not illiadFlag:
			# Make the intro
			tempText = emailIntroText3Recall
			tempText = buildEmailIntro(circ3Recall[index-1],tempText)

			if 	not circ3Recall[index-1]["Email"] or \
				not emailPattern.match(circ3Recall[index-1]["Email"]):
				# If no email address, or invalid format, give Postal address, if present
					recallCount["noEmailCount"] += 1

		try:
			# add 2nd part of template
			tempText += emailItemText3Recall

			# fill in the first items details
			tempText  = addEmailItem(circ3Recall[index-1],tempText)
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding recall item to email text, notice is  " + str(circ3Recall[index-1]))

		# Add item to summary csv
		try:
			addToSummaryCsv(tmpLocation + csvFile,circ3Recall[index-1],"RECALL")
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding recall item (1st) to  CSV File, notice is  " + str(circ3Recall[index-1]))

		# is the next item also for the same email address, then fill them out in the same email!
		# ALSO CHECK FIRST NAME, otherwise we lump all no-email people into one!
		while (index < len(circ3Recall)) and \
			(circ3Recall[index]["Email"]     == circ3Recall[index-1]["Email"]) and \
			(circ3Recall[index]["FirstName"] == circ3Recall[index-1]["FirstName"]) and \
			(circ3Recall[index]["LastName"]  == circ3Recall[index-1]["LastName"]):
				index += 1    # move to the next.
				if illiadFlag:
					# if it's an ILL item, throw into the CSV
					recallCount["ill"] += 1

					try:
						addToIllCsv(tmpLocation + recallIlliadFile, circ3Recall[index-1])
					except Exception, e:
						print repr(e)
						errorLogger("MINOR", repr(e) + "error adding Recall item to Recall ILL CSV File, notice is " + str(circ3Recall[index-1]))
				else:
					try:
						recallCount["itemCount"]        += 1
						tempText += emailItemText3Recall
						tempText  = addEmailItem(circ3Recall[index-1],tempText)
					except Exception, e:
						print repr(e)
						errorLogger("MINOR", repr(e) + "error adding Recall item to email notice is " + str(circ3Recall[index-1]))

					# Add item to summary csv
					try:
						addToSummaryCsv(tmpLocation + csvFile,circ3Recall[index-1],"RECALL")
					except Exception, e:
						print repr(e)
						errorLogger("MINOR", repr(e) + "error adding Recall 2nd to Summary CSV File notice is" + str(circ3Recall[index-1]) )

		# Lastly, add the standard footer.
		tempText += emailFooterText3Recall

		tempText = tempText.replace("[{!LIBNUM!}]", "JPL Front Desk  - 210-458-4574\n\t\tDTL Front Desk  - 210-458-2440")

		# Time to check if we have an email address

		if (not circ3Recall[index-1]["Email"] or not emailPattern.match(circ3Recall[index-1]["Email"])) \
			and not illiadFlag:
			# first add RTF line breaks
			tt2 = ""

			for line in tempText.splitlines():
				tt2 += line + "\line\n"

			printableDoc3Recall += tt2 + "\line \page"
			printableDoc3RecallFlag = 1
		elif illiadFlag:
			# waiting on Anne to decide what she wants done with ILL
			pass
		else:
			# email text constructed, function to parse email address and send.
			try:
				sendEmail(tempText,circ3Recall[index-1]["Email"],"Your library item has been recalled")
			except Exception, e:
				print repr(e)
				errorLogger("MINOR", repr(e) + "error sending recall file for item id of" + str(circ3Recall[index-1]))

		# clear illiad flag for next iteration
		illiadFlag = 0

        #######################
        # END OF RECALL LOOP #
        #######################

if printableDoc3RecallFlag:
	# Have recall notices with no email address to print? Create RTF and send
	printableDoc3Recall += "}" # close the RTF if we made one
	try:
		f = open(tmpLocation + printableRecallFile,"wb")
		f.write(printableDoc3Recall)
		f.close()
		sendEmailPrintable("Recall notices requiring manual printing",printableRecallFile, printableRecallTo, tmpLocation,"Recall notices requiring manual printing")
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error sending Recall printable File")


if recallCount["ill"] > 0:
	try:
		sendEmailPrintable("ILL items Recalled in Voyager",recallIlliadFile,illiadEmail, tmpLocation, "Recalled ILL Items within Voyager")
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error sending recall ILL CSV File")
##################
# END OF RECALL  #
##################

##################################
# OVERDUERECALL PROCESSING START #
##################################
############################
# Parse circ4Overduerecall #
############################

index = 0

# build the text of each email
tempText = ""

# Illiad detected flag
illiadFlag = 0

# replacing iterable for look with while loop, so easier to skip when same email address found by increasing index.
while index < len(circ4Overduerecall):
	index += 1

	# Check for Illiad user
	if circ4Overduerecall[index-1]["FirstName"] == illiadFirst:
		illiadFlag        			= 1
		overdueRecallCount["ill"]  += 1

		# note, period extra on itemId to force not scientific notation
		try:
			addToIllCsv(tmpLocation + overdueRecallIlliadFile, circ4Overduerecall[index-1])
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding overdue recall item to  CSV File, notice is " + str(circ4Overduerecall[index-1]))

	else:
		overdueRecallCount["personCount"] += 1
		overdueRecallCount["itemCount"]   += 1

	if not illiadFlag:
		# regular item, not illiad, so set the header area
		# Make the intro
		tempText = emailIntroText4Overduerecall
		tempText = buildEmailIntro(circ4Overduerecall[index-1],tempText)

		if	not circ4Overduerecall[index-1]["Email"] or \
			not emailPattern.match(circ4Overduerecall[index-1]["Email"]):
				# If no email address, or invalid format, give Postal address, if present
				overdueRecallCount["noEmailCount"] += 1

	try:
		# add 2nd part of template
		tempText += emailItemText4Overduerecall

		# fill in the fields
		tempText  = addEmailItem(circ4Overduerecall[index-1],tempText)
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error adding overdue recall item to email, notice is " + str(circ4Overduerecall[index-1]))

	# Add item to summary csv
	try:
		addToSummaryCsv(tmpLocation + csvFile,circ4Overduerecall[index-1],"OVERDUERECALL")
	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error adding overdue recall item (1) to  CSV File, notice is " + str(circ4Overduerecall[index-1]))

	# is the next item also for the same email address, then fill them out in the same email!
	# ALSO CHECK FIRST NAME, otherwise we lump all no-email people into one!
	while (index < len(circ4Overduerecall)) and \
		(circ4Overduerecall[index]["Email"]     == circ4Overduerecall[index-1]["Email"]) and \
		(circ4Overduerecall[index]["FirstName"] == circ4Overduerecall[index-1]["FirstName"]) and \
		(circ4Overduerecall[index]["LastName"]  == circ4Overduerecall[index-1]["LastName"]):
			index   += 1    # move to the next.
			if illiadFlag:
				# if it's an ILL item, throw into the CSV
				overdueRecallCount["ill"]     += 1

				try:
					addToIllCsv(tmpLocation + overdueRecallIlliadFile, circ4Overduerecall[index-1])
				except Exception, e:
					print repr(e)
					errorLogger("MINOR", repr(e) + "error adding overdue recall item to ILL CSV File, ItemID " + str(circ4Overduerecall[index-1]))
			else:
				overdueRecallCount["itemCount"]        += 1

				try:
					tempText += emailItemText4Overduerecall
					tempText  = addEmailItem(circ4Overduerecall[index-1],tempText)

				except Exception, e:
					print repr(e)
					errorLogger("MINOR", repr(e) + "Error adding item email, Overduerecall, notice is  : " + str(circ4Overduerecall[index-1]))

				# Add item to summary csv
				try:
					addToSummaryCsv(tmpLocation + csvFile,circ4Overduerecall[index-1],"OVERDUERECALL")
				except Exception, e:
					print repr(e)
					errorLogger("MINOR", repr(e) + "error adding overdue recall item (2) to  CSV File, ItemID " + str(circ4Overduerecall[index-1]))


			# Lastly, add the standard footer.
			tempText += emailFooterText4Overduerecall
			tempText = tempText.replace("[{!LIBNUM!}]", "JPL Front Desk  - 210-458-4574\n\t\tDTL Front Desk  - 210-458-2440")

			# Time to check if we have an email address
			if (not circ4Overduerecall[index-1]["Email"] or not emailPattern.match(circ4Overduerecall[index-1]["Email"])) \
				and not illiadFlag:
					# first add RTF line breaks
					tt2 = ""
					for line in tempText.splitlines():
						tt2 += line + "\line\n"

					printableDoc4Overduerecall += tt2 + "\line \page"
					printableDoc4OverduerecallFlag = 1

			elif illiadFlag:
				# no need here
				pass
			else:
				# email text constructed, function to parse email address and send.
				sendEmail(tempText,circ4Overduerecall[index-1]["Email"],"Your recalled library item is overdue!")

	# clear illiad flag for next iteration
	illiadFlag = 0

	#############################
	# END OF OVERDUERECALL LOOP #
	#############################

if printableDoc4OverduerecallFlag:
	# Have recall notices with no email address to print? Create RTF and send
	printableDoc4Overduerecall += "}" # close the RTF if we made one

	try:
		f = open(tmpLocation + printableOverduerecallFile,"wb")
		f.write(printableDoc4Overduerecall)
		f.close()

		sendEmailPrintable("Overdue Recall notices requiring manual printing",printableOverduerecallFile, printableOverduerecallTo, tmpLocation,"Overdue Recall notices requiring manual printing")

	except Exception, e:
		print repr(e)
		errorLogger("MAJOR", repr(e) + "error closing/sending overdue recall printable doc")

if overdueRecallCount["ill"] > 0:
	try:
		f = open(tmpLocation + overduerecallIlliadFile,"w")
		f.write(overduerecallIlliadCSV)
		f.close()

		sendEmailPrintable("Overdue ILL items Recalled in Voyager",overduerecallIlliadFile,illiadEmail, tmpLocation, "Overdue Recalled ILL Items within Voyager")

	except Exception, e:
		print repr(e)
		errorLogger("MAJOR", repr(e) + "error closing/sending overdue recall ILL doc")


#########################
# END OF OVERDUERECALL  #
#########################

##############################
# FINE/FEE NOTICE PROCESSING #
##############################
########################
# Parse circ5Finesfees #
########################


# used for traversing circ3Recall list of dicts
index = 0

# build the text of each email
tempText = ""

# Illiad detected flag
illiadFlag = 0

# replacing iterable for look with while loop, so easier to skip when same email address found by increasing index.
while index < len(circ5Finesfees):
	index += 1

	# Check for Illiad user
	if circ5Finesfees[index-1]["FirstName"] == illiadFirst:
		illiadFlag        = 1
		pass    # dont care about ILL user having fines
	else:
		finesFeesCount["personCount"] += 1
		finesFeesCount["itemCount"]   += 1

	if not illiadFlag:
		# regular item, not illiad, so set the header area
		# Make the intro
		tempText = emailIntroText5Finesfees
		tempText = buildEmailIntro(circ5Finesfees[index-1],tempText)

		if not circ5Finesfees[index-1]["Email"] or \
			not emailPattern.match(circ5Finesfees[index-1]["Email"]):
				# If no email address, or invalid format, give Postal address, if present
				finesFeesCount["noEmailCount"] += 1


		# add 2nd part of template
		tempText += emailItemText5Finesfees

		# fines and fees takes additional items
		tempText = addFineEmail(circ5Finesfees[index-1],tempText)

		# Add item to summary csv
		try:
			addToSummaryCsv(tmpLocation + csvFile,circ5Finesfees[index-1],"FINEFEE")
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding fine fee item to summary (1) CSV File, ItemID " + str(circ5Finesfees[index-1]))

		# is the next item also for the same email address, then fill them out in the same email!
		# ALSO CHECK FIRST NAME, otherwise we lump all no-email people into one!
		while (index < len(circ5Finesfees)) and \
			(circ5Finesfees[index]["Email"]     == circ5Finesfees[index-1]["Email"]) and \
			(circ5Finesfees[index]["FirstName"] == circ5Finesfees[index-1]["FirstName"]) and \
			(circ5Finesfees[index]["LastName"]  == circ5Finesfees[index-1]["LastName"]):
				index   += 1    # move to the next.
				if not illiadFlag:
					finesFeesCount["itemCount"]        += 1

					tempText += emailItemText5Finesfees

					# fines and fees takes additional items
					tempText = addFineEmail(circ5Finesfees[index-1],tempText)

					try:
						# Add item to summary csv
						addToSummaryCsv(tmpLocation + csvFile,circ5Finesfees[index-1],"FINEFEE")
					except Exception, e:
						print repr(e)
						errorLogger("MINOR", repr(e) + "error adding fine fee item to summary (2) CSV File, notice line is " + str(circ5Finesfees[index-1]))

		# Lastly, add the standard footer.
		tempText += emailFooterText5Finesfees

		tempText = tempText.replace("[{!LIBNUM!}]", "JPL Front Desk  - 210-458-4574\n\t\tDTL Front Desk  - 210-458-2440")

		# Time to check if we have an email address
		if (not circ5Finesfees[index-1]["Email"] or not emailPattern.match(circ5Finesfees[index-1]["Email"])) \
			and not illiadFlag:
				# first add RTF line breaks
				tt2 = ""
				for line in tempText.splitlines():
					tt2 += line + "\line\n"

				printableDoc5FinesFees += tt2 + "\line \page"
				printableDoc5FinesFeesFlag = 1

		elif not illiadFlag:
			# No fines and fees for ILL

			# email text constructed, function to parse email address and send.
			sendEmail(tempText,circ5Finesfees[index-1]["Email"],"There is a fine on your library account")

		# clear illiad flag for next iteration
		illiadFlag = 0

if printableDoc5FinesFeesFlag:
	# Have recall notices with no email address to print? Create RTF and send
	printableDoc5FinesFees += "}" # close the RTF if we made one

	try:
		f = open(tmpLocation + printableFinesFeesFile,"wb")
		f.write(printableDoc5FinesFees)
		f.close()

		sendEmailPrintable("Fine/Fee notices requiring manual printing",printableFinesFeesFile, printableFinesFeesTo, tmpLocation,"Fine/Fee notices requiring manual printing")

	except Exception, e:
		print repr(e)
		errorLogger("MINOR", repr(e) + "error writing/sending fine fee printable file")

#####################################
# END OF FINE/FEE NOTICE PROCESSING #
#####################################

##################################
# COURTESY PROCESSING START #
##################################
########################
# Parse circ7Courtesy  #
#########################

# used for traversing circ7Courtesy list of dicts
index = 0

# build the text of each email
tempText = ""

# Illiad detected flag
illiadFlag = 0

# replacing iterable for look with while loop, so easier to skip when same email address found by increasing index.
while index < len(circ7Courtesy):
	index += 1

	# Check for Illiad user
	if circ7Courtesy[index-1]["FirstName"] == illiadFirst:
		pass # do nothing with ILL items that arent overdue yet
	else:
		courtesyCount["personCount"] += 1
		courtesyCount["itemCount"]   += 1

	if not illiadFlag:
		
		# regular item, not illiad, so set the header area
		# Make the intro
		tempText = emailIntroText7Courtesy
		tempText = buildEmailIntro(circ7Courtesy[index-1],tempText)

		if not circ7Courtesy[index-1]["Email"] or \
			not emailPattern.match(circ7Courtesy[index-1]["Email"]):
				# If no email address, or invalid format, give Postal address, if present
				courtesyCount["noEmailCount"] += 1

		# add 2nd part of template
		tempText += emailItemText7Courtesy

		# fill in the first items details
		tempText = tempText.replace("[{!LOC!}]",   circ7Courtesy[index-1]["Library"].lstrip(" "))
		tempText = tempText.replace("[{!TITLE!}]", circ7Courtesy[index-1]["ItemTitle"].lstrip(" "))
		tempText = tempText.replace("[{!AUTHOR!}]",circ7Courtesy[index-1]["ItemAuthor"].lstrip(" "))
		tempText = tempText.replace("[{!ITEMID!}]",circ7Courtesy[index-1]["ItemId"].lstrip(" "))
		tempText = tempText.replace("[{!CALL!}]",  circ7Courtesy[index-1]["ItemCall"].lstrip(" "))
		tempText = tempText.replace("[{!DUE!}]",   circ7Courtesy[index-1]["DueDate"].lstrip(" "))

		# Add item to summary csv
		try:
			addToSummaryCsv(tmpLocation + csvFile,circ7Courtesy[index-1],"COURTESY")
		except Exception, e:
			print repr(e)
			errorLogger("MINOR", repr(e) + "error adding courtesy item to summary CSV (1) File, notice line is " + str(circ7Courtesy[index-1]))

		# is the next item also for the same email address, then fill them out in the same email!
		# ALSO CHECK FIRST NAME, otherwise we lump all no-email people into one!
		while (index < len(circ7Courtesy)) and \
			(circ7Courtesy[index]["Email"]     == circ7Courtesy[index-1]["Email"]) and \
			(circ7Courtesy[index]["FirstName"] == circ7Courtesy[index-1]["FirstName"]) and \
			(circ7Courtesy[index]["LastName"]  == circ7Courtesy[index-1]["LastName"]):
				index   += 1    # move to the next.

				if illiadFlag:
					pass # do nothing with illiad items not yet overdue

				else:
					courtesyCount["itemCount"] += 1
					tempText += emailItemText7Courtesy
					tempText = tempText.replace("[{!LOC!}]",    circ7Courtesy[index-1]["Library"].lstrip(" "))
					tempText = tempText.replace("[{!TITLE!}]",  circ7Courtesy[index-1]["ItemTitle"].lstrip(" "))
					tempText = tempText.replace("[{!AUTHOR!}]", circ7Courtesy[index-1]["ItemAuthor"].lstrip(" "))
					tempText = tempText.replace("[{!ITEMID!}]", circ7Courtesy[index-1]["ItemId"].lstrip(" "))
					tempText = tempText.replace("[{!CALL!}]",   circ7Courtesy[index-1]["ItemCall"].lstrip(" "))
					tempText = tempText.replace("[{!DUE!}]",    circ7Courtesy[index-1]["DueDate"].lstrip(" "))

					# Add item to summary csv
					try:
						addToSummaryCsv(tmpLocation + csvFile,circ7Courtesy[index-1],"COURTESY")
					except Exception, e:
						print repr(e)
						errorLogger("MINOR", repr(e) + "error adding courtesy item to summary (2) CSV File, notice line is " + str(circ7Courtesy[index-1]))

		# Lastly, add the standard footer.
		tempText += emailFooterText7Courtesy

		tempText = tempText.replace("[{!LIBNUM!}]", "JPL Front Desk  - 210-458-4574\n\t\tDTL Front Desk  - 210-458-2440")

		# Time to check if we have an email address
		if (not circ7Courtesy[index-1]["Email"] or not emailPattern.match(circ7Courtesy[index-1]["Email"])) \
			and not illiadFlag:
				# first add RTF line breaks
				tt2 = ""

				for line in tempText.splitlines():
					tt2 += line + "\line\n"

				printableDoc7Courtesy += tt2 + "\line \page"
				printableDoc7CourtesyFlag = 1

		elif illiadFlag:
			# no action if ILL courtesy
			pass
		else:
			# email text constructed, function to parse email address and send.
			sendEmail(tempText,circ7Courtesy[index-1]["Email"],"Your library item is due soon")

		# clear illiad flag for next iteration
		illiadFlag = 0

		########################
		# END OF COURTESY LOOP #
		########################

if printableDoc7CourtesyFlag:
	# Have recall notices with no email address to print? Create RTF and send
	printableDoc7Courtesy += "}" # close the RTF if we made one

	try:
		f = open(tmpLocation + printableCourtesyFile,"wb")
		f.write(printableDoc7Courtesy)
		f.close()

		sendEmailPrintable("Courtesy notices requiring manual printing",printableCourtesyFile, printableCourtesyTo, tmpLocation,"Courtesy notices requiring manual printing")

	except Exception, e:
		print repr(e)
		errorLogger("MAJOR", repr(e) + "error saving/sending courtesy item printable file")

###################
# END OF COURTESY #
###################


summaryForManagers()

# send the summary file
sendEmailPrintable("Summary of circulation notices CSV",csvFile, csvSummaryTo, tmpLocation,"CSV file summary of todays circulation notices")

# Rename file with date/time if we did this run
dateString =    time.strftime("%Y%m%d.%H%M")

if not overideEmail:
	os.rename(noticesFile,noticesFile + "." + dateString)
else:
	print "didnt rename"
