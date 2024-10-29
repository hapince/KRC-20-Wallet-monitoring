import streamlit as st
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

# Email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 465
sender_email = "happy.prince.max@gmail.com"  # Sender's email
receiver_email = "17300766401@163.com"  # Receiver's email
password = "unpn umpg hvzg elxe"  # App-specific password

# URL to monitor
url = "https://kasplex.org/Currency?address=kaspa:qr5ersqcxrpphkz24k389c9ewtfeh007naglgfjztzr9rpgwv4gd52jj2dzfv"

# Function to send an email notification
def send_email(token_data):
    try:
        # Construct email content
        html_content = "<h2>KRC-20 Token Monitoring Notification</h2><table border='1'><tr><th>Token Name</th><th>Amount</th></tr>"
        for token, amount in token_data.items():
            html_content += f"<tr><td>{token}</td><td>{amount}</td></tr>"
        html_content += "</table>"

        msg = MIMEText(html_content, "html")  # Sending HTML-formatted email
        msg['Subject'] = 'KRC-20 Token Monitoring Notification'
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        st.success("Email sent successfully!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

# Function to scrape token data
def scrape_tokens():
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find table body with tokens
    tokens_table_body = soup.find('tbody', class_='ant-table-tbody')
    token_data = {}

    if tokens_table_body:
        # Iterate over each row to find token data
        for row in tokens_table_body.find_all('tr', class_='ant-table-row ant-table-row-level-0'):
            # Get token name and clean the 'Fair Mint' part
            token_name_with_span = row.find('td', class_='ant-table-cell searchCell').get_text(strip=True)
            token_name = token_name_with_span.split('Fair Mint')[0].strip()
            token_amount = row.find_all('td', class_='ant-table-cell deployTime')[1].get_text(strip=True)
            token_data[token_name] = token_amount

        # Display the data in Streamlit
        st.write("### Current Tokens Data")
        st.write(token_data)

        # Option to send email
        if st.button("Send Email Notification"):
            send_email(token_data)
    else:
        st.warning("Token table body not found. Please check the page structure.")

# Streamlit layout
st.title("KRC-20 Token Monitor")
st.write("Click 'Scrape Token Data' to fetch and view the latest token data.")

# Scrape token data on button click
if st.button("Scrape Token Data"):
    scrape_tokens()
