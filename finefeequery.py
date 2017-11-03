#!/usr/local/bin/python

############################
# finesfeesquery.py
# Written by: Bruce Orcutt
# 5/4/2016
# Purpose: Replaces Access database used by Access Services to list outstanding fines and fees.
# queries database, and outputs a CSV file, that's emailed to a hard coded email address.
# 1/2/17 added circulation.edu to outgoing per adam zaby
# 1/2/17 fixed bug when user has no banner account
# 3/16/17 total fines (not just weekly)
# 11/3/17 clean up code for github release

import csv
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import encoders
import smtplib
import cx_Oracle
import sys


#############
# CONSTANTS #
#############
addressToSend			= "destination.address@xxx.yyy, seperate.new.users@with.commas"
tmpLocation 			= "/tmp/"
csvFFFile				= "FinesFeesSummary.csv"
printableFromAddress 	= "From.Address@to.send.from"
emailServer				= "localhost"


def findTotal(patronID):
	# function to get the total amount of fines owed for a patron, not just the weekly fines
	# Does lookup based on patron id
	sum = 0.0;

	# make connection to the database
	dsn = cx_Oracle.makedsn("localhost","1521","VGER")
	con = cx_Oracle.connect(user="READ-ONLY-DBA-USER",password="READ-ONLY-DBA-PASS",dsn=dsn)
	cur = con.cursor()

	# run the query
	query = """
			SELECT sum(fine_fee_balance)
			FROM fine_fee
			WHERE patron_id='{pID}'
	"""

	cur.execute(query.format(pID=patronID));

	try:
		sum	= cur.fetchone()[0]
	except:
		sum  = 0.0

	return sum

def sendEmailPrintable(textToSend,fileToSend,addressToSend, pathToFile, subject):
        msg             = MIMEMultipart()
        msg['From']     = printableFromAddress
        msg['To']       = addressToSend
        msg['Subject']  = subject

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
        server.sendmail(printableFromAddress, addressToSend.split(","), text)
        server.quit
        attachment.close()

dsn = cx_Oracle.makedsn("localhost","1521","VGER")
con = cx_Oracle.connect(user="READ-ONLY-DBA-USER",password="READ-ONLY-DBA-PASS",dsn=dsn)

cursor = con.cursor()

cursor.execute("""
SELECT
    pt.ssan,
    pt.last_name,
    pt.first_name,
    pt.institution_id,
    ib.item_barcode,
    bt.title,
    ff.fine_fee_amount as Amount,
    ft.fine_fee_desc,
    to_char(ff.due_date,'mm/dd/yyyy') as DueDate,
    to_char(ff.fine_fee_notice_date,'mm/dd/yyyy') as FineFeeNoticeDate,
    lc.location_name as fine_fee_location,
    pt.patron_id
  FROM
    fine_fee ff,
    fine_fee_type ft,
    location lc,
    item_barcode ib,
    bib_item bi,
    bib_text bt,
    patron pt
  WHERE
		to_char(fine_fee_notice_date,'mm/dd/yyyy')=to_char(sysdate, 'mm/dd/yyyy')
--	to_char(fine_fee_notice_date,'mm/dd/yyyy')='03/10/2017'
    AND   ff.fine_fee_type=ft.fine_fee_type
    AND   ff.fine_fee_location = lc.location_id
    AND   ib.item_id=ff.item_id
    AND   ib.barcode_status=1
    AND   bi.item_id=ff.item_id
    AND   bi.bib_id=bt.bib_id
    AND   ff.patron_id=pt.patron_id
  ORDER BY ssan, ff.due_date
"""

)

# fines and fees CSV file
csvFFFileIter  = open(tmpLocation + csvFFFile, 'w')
csvWriterFF = csv.writer(csvFFFileIter,dialect='excel')
csvHeaderFF = ["Banner ID","Last Name","First Name","ABC123","Barcode","Title","Amount","Description","Due Date","Notice Date","Location"]
csvWriterFF.writerow(csvHeaderFF)


sumList = []
lastBanner = 0
index = 0


for result in cursor:

	tempdict = dict()

	# is this same user as last row?
	if lastBanner == result[0]:
		# same user, add
		sumList[index-1]["Amount"] += result[6]
	else:
		# new user
		sumList.append(tempdict)
		testString			  	= result[0]
		if testString != None:
			sumList[index]["BannerID"]    = testString[1:]
		else:
			sumList[index]["BannerID"]    = "NONE"
		sumList[index]["LastName"]  	= result[1]
		sumList[index]["FirstName"] 	= result[2]
		sumList[index]["Amount"] 	= result[6]
		sumList[index]["PatronID"] 	= result[11] # for grand totals below
		index += 1

	result2 = list(result)  # leave out patron id for first csv file section
	if result2[0] != None:
		result2[0] = "@" + result2[0][1:]  # format of UTSA Banner IDs
	else:
		result2[0] = "NONE" # community users, alumni, etc

	result2[4] = "'" + result2[4]   # for id, want it to be read as a text field in excel, but pure number.
	result2[6] = "$" + str(int(result2[6])/100.0)
	result2  += [result[0]]
	csvWriterFF.writerow(result2[0:11])

	lastBanner = result[0]

csvWriterFF.writerow("  ")
csvWriterFF.writerow(["TOTALS FOR USERS"])
csvWriterFF.writerow(["================"])
csvWriterFF.writerow(["Banner ID","Last Name","First Name","Report Total","Total Due"])

for fine in sumList:
	if fine["BannerID"] == "NONE":
		csvWriterFF.writerow([fine["BannerID"],fine["LastName"],fine["FirstName"],"$" + str(int(fine["Amount"])/100.0),"$" + str(int(findTotal(fine["PatronID"]))/100.0)])
	else:
		csvWriterFF.writerow(["@" + fine["BannerID"],fine["LastName"],fine["FirstName"],"$" + str(int(fine["Amount"])/100.0),"$" + str(int(findTotal(fine["PatronID"]))/100.0)])

csvFFFileIter.close()
cursor.close()

sendEmailPrintable("Outstanding Fines and Fees Report",csvFFFile,addressToSend, tmpLocation,"Outstanding Fines and Fees CSV Report" )
