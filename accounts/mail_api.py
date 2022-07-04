import imaplib

def create_account():

    pass




def parse_page():
    mail = imaplib.IMAP4_SSL('imap.googlemail.com')
    mail.login('nikitamastinen@gmail.com', 'nikitamas')
    mail.list()

    status, messages = mail.select("inbox")
    # number of top emails to fetch
    N = 1
    # total number of emails
    messages = int(messages[0])

    try:
        for i in range(messages, messages - N, -1):
            res, msg = mail.fetch(str(i), "(RFC822)")
            for response in msg:
                print(response)
                print("++++++++++++++++++++++++++++++++++++++++++++++++")
            print("____________")

    except imaplib.IMAP4.error:
        print("All fetched")

    mail.close()
    mail.logout()

parse_page()