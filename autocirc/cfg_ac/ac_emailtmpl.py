# preformated text to use for emails for overdue notices
#[{! brackets are strings to be replaced with .replace

####Overdue
emailIntroText2Overdue  = """
[{!DATE!}]

[{!INSTNAME!}]

[{!POSTAL!}]

Dear [{!FNAME!}] [{!LNAME!}]:

\tThe following item(s) is overdue.

"""
emailItemText2Overdue   = """
                Title:\t\t\t[{!TITLE!}]
                Author:\t\t\t[{!AUTHOR!}]
                Barcode:\t\t[{!ITEMID!}]
                Call #:\t\t\t[{!CALL!}]
                Due Date:\t\t[{!DUE!}]
                Notification #:\t\t[{!NOT!}]
                Location:\t\t[{!LOC!}]

"""
emailFooterText2Overdue = """

\tIf the item is no longer needed, please return it to any YOUR library location in order to avoid accumulation of fines.

\tOr, you can renew your item(s) in person, over the phone, or online by logging in to your library account:
\thttps://address-to-library-account/page.html

\tHave a question? Contact us:
\t\tPhone:\t\t[{!LIBNUM!}]
"""

######Recall
emailIntroText3Recall  = """
[{!DATE!}]

[{!INSTNAME!}]

[{!POSTAL!}]

Dear [{!FNAME!}] [{!LNAME!}]:

\tThe following item currently checked out to you has been recalled. The new due date is shown below.

"""

emailItemText3Recall   = """

                Title:\t\t\t[{!TITLE!}]
                Author:\t\t\t[{!AUTHOR!}]
                Barcode:\t\t[{!ITEMID!}]
                Call #:\t\t\t[{!CALL!}]
                Due Date:\t\t[{!DUE!}]
                Location:\t\t[{!LOC!}]

"""

emailFooterText3Recall = """
\tThank you for returning the item to any YOUR library location by the new due date.

\tHave a question? Contact us:
\t\tPhone:\t\t[{!LIBNUM!}]

"""

########OverdueRecall
emailIntroText4Overduerecall  = """
[{!DATE!}]

[{!INSTNAME!}]

[{!POSTAL!}]

Dear [{!FNAME!}] [{!LNAME!}]:

        Please return the following recalled item(s) to any YOUR library location as soon as possible.

"""

emailItemText4Overduerecall   = """

                Title:\t\t\t[{!TITLE!}]
                Author:\t\t\t[{!AUTHOR!}]
                Barcode:\t\t[{!ITEMID!}]
                Call #:\t\t\t[{!CALL!}]
                Due Date:\t\t[{!DUE!}]
                Location:\t\t[{!LOC!}]

"""

emailFooterText4Overduerecall = """
\tFines for overdue recalled items are higher than regular fines and increase the longer you keep the item. Thank you for returning the item(s) as soon as possible.

\tHave a question? Contact us:
\t\tPhone:\t\t[{!LIBNUM!}]

"""

#########FinesFees

emailIntroText5Finesfees  = """
[{!DATE!}]

[{!INSTNAME!}]

[{!POSTAL!}]

Dear [{!FNAME!}] [{!LNAME!}]:

        Below is a list of current library fines on your account.

        You can pay by personal check, YOUR Card, or Guest Card at the X Library or the Y Library. You can pay by cash or credit card (A and B only) at the Fiscal Services location on either campus.

        If you would like more detailed information regarding your fines, or if you have a question or need help, please contact us.


"""

emailItemText5Finesfees   = """

\t\t\tTitle:\t\t\t\t[{!TITLE!}]
\t\t\tAuthor:\t\t\t\t[{!AUTHOR!}]
\t\t\tBarcode:\t\t\t[{!ITEMID!}]
\t\t\tCall #:\t\t\t\t[{!CALL!}]
\t\t\tLocation:\t\t\t[{!LOC!}]
\t\t\tDue Date:\t\t\t[{!DUE!}]
\t\t\tDue Date when Fined:\t\t[{!DDWF!}]
\t\t\tFine/Fee Date:\t\t\t[{!CDATE!}]
\t\t\tDescription:\t\t\t[{!DESC!}]
\t\t\tFine/Fee Amount:\t\t[{!FFA!}]
\t\t\tFine/Fee Balance:\t\t[{!FFB!}]
\t\t\tPreviously Billed:\t\t[{!PB!}]

\t\t\tTotal of Fines/Fees:\t\t[{!TFF!}]

"""

emailFooterText5Finesfees = """
\tHave a question? Contact us:
\t\tPhone:\t\t[{!LIBNUM!}]
"""

#####Courtesy
emailIntroText7Courtesy  = """
[{!DATE!}]

[{!INSTNAME!}]

[{!POSTAL!}]

Dear [{!FNAME!}] [{!LNAME!}]:

\t\tJust a reminder that the following item(s) will be due soon.

"""

emailItemText7Courtesy   = """


\t\t\tTitle:\t\t\t[{!TITLE!}]
\t\t\tAuthor:\t\t\t[{!AUTHOR!}]
\t\t\tBarcode:\t\t[{!ITEMID!}]
\t\t\tCall #:\t\t\t[{!CALL!}]
\t\t\tDue Date:\t\t[{!DUE!}]
\t\t\tLocation:\t\t[{!LOC!}]

"""

emailFooterText7Courtesy = """
\tPlease return the item(s) or renew by the due date in order to avoid fines. You can renew your item(s) in person, over the phone, via our mobile site, or online by logging in to your library account:
\t\thttps://address-to-library-account/page.html

\tHave a question? Contact us:
\t\tPhone:\t\t[{!LIBNUM!}]

"""
