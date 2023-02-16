import os

import requests
import lxml.html as lh
import pandas as pd
from os.path import exists
import smtplib
from email.message import EmailMessage

headers = ["Section","Section2","Section3"]
def get_pdf():
    resp = requests.get(
        "https://www.galaxie.enseignementsup-recherche.gouv.fr/ensup/ListesPostesPublies/Emplois_publies_TrieParCorps.html")
    # Create a handle, page, to handle the contents of the website
    doc = lh.fromstring(resp.content)  # Parse data that are stored between <tr>..</tr> of HTML
    tr_elements = doc.xpath("//table[contains(@class, 'tab')]/tr")
    # Check the length of the first 12 rows
    # Create empty list
    col = []
    i = 0  # For each row, store each first element (header) and an empty list
    # For each row, store each first element (header) and an empty list
    for t in tr_elements[0]:
        i += 1
        name = t.text_content().strip()
        col.append((name, []))
    # Since out first row is the header, data is stored on the second row onwards
    links = doc.xpath("//a")
    for j in range(1, len(tr_elements)):
        # T is our j'th row
        T = tr_elements[j]
        # If row is not of size 10, the //tr data is not from our table
        if len(T) != 16:
            break

        current_link = links[j - 1].get("href")
        # i is the index of our column
        i = 0
        # Iterate through each element of the row
        for t in T.iterchildren():
            data = t.text_content()
            # Append the data to the empty list of the i'th column
            if i == 2:
                col[i][1].append(current_link)
            elif col[i][0].startswith("Section") and data:
                col[i][1].append(int(data))
            else:
                col[i][1].append(data)
            # Increment i for the next column
            i += 1
    Dict = {title: column for (title, column) in col}
    df = pd.DataFrame(Dict)
    df.head()
    urls = list()
    for header in headers:
        rslt_df = df.loc[(df[header] == 32) | (df[header] == 86)]
        urls.extend([url for url in rslt_df['Référence GALAXIE']])

    return urls


def download_new_pdf(urls):
    new_offers = list()
    for url in urls:
        name = url.rsplit('/', 1)[-1]
        if not exists(name):
            r = requests.get(url, stream=True)
            with open(f'./{name}', 'wb') as f:
                f.write(r.content)
                new_offers.append(url)
    return new_offers


def send_email(urls):
    if not os.getenv("GMAIL_SENDER") or not os.getenv("GMAIL_PASSWORD") or not os.getenv("GMAIL_RECEIVER"):
        print("Missing env var, check readme")
        return

    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(os.getenv("GMAIL_SENDER"), os.getenv("GMAIL_PASSWORD"))

    # message to be sent
    formated = "\n".join(urls)

    message = f"De nouvelles offres sont disponibles sur galaxies:\n {formated}"
    msg = EmailMessage()
    msg['Subject'] = "Offres Galaxies"
    msg['From'] = os.getenv("GMAIL_SENDER")
    msg['To'] = os.getenv("GMAIL_RECEIVER")
    msg.set_content(message)

    s.send_message(msg)

    # terminating the session
    s.quit()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    offers = download_new_pdf(get_pdf())
    if offers:
        print(f"New offers: {offers}")
        send_email(offers)
