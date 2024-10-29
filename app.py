# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "happy.prince.max@gmail.com")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "17300766401@163.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "unpn umpg hvzg elxe")

# Monitoring configuration
KASPA_URL = "https://kasplex.org/Currency?address=kaspa:qr5ersqcxrpphkz24k389c9ewtfeh007naglgfjztzr9rpgwv4gd52jj2dzfv"
REFRESH_INTERVAL = 60  # seconds

# scraper.py
import time
from typing import Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import KASPA_URL

class TokenScraper:
    def __init__(self):
        self.driver = None

    def start_driver(self):
        if not self.driver:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = uc.Chrome(options=options)

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def scrape_tokens(self) -> Dict[str, str]:
        try:
            if not self.driver:
                self.start_driver()
            
            self.driver.get(KASPA_URL)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'ant-table-tbody'))
            )
            time.sleep(3)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            tokens_table_body = soup.find('tbody', class_='ant-table-tbody')
            
            token_data = {}
            if tokens_table_body:
                for row in tokens_table_body.find_all('tr', class_='ant-table-row ant-table-row-level-0'):
                    token_name_with_span = row.find('td', class_='ant-table-cell searchCell').get_text(strip=True)
                    token_name = token_name_with_span.split('Fair Mint')[0].strip()
                    token_amount = row.find_all('td', class_='ant-table-cell deployTime')[1].get_text(strip=True)
                    token_data[token_name] = token_amount

            return token_data

        except Exception as e:
            print(f"Scraping error: {e}")
            return {}

# email_handler.py
import smtplib
from email.mime.text import MIMEText
from typing import Dict
from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, RECEIVER_EMAIL, EMAIL_PASSWORD

class EmailHandler:
    @staticmethod
    def send_email(token_data: Dict[str, str]) -> bool:
        try:
            html_content = """
            <h2>KRC-20 Token 监控通知</h2>
            <table border='1'>
                <tr>
                    <th>Token 名称</th>
                    <th>数量</th>
                </tr>
            """
            
            for token, amount in token_data.items():
                html_content += f"<tr><td>{token}</td><td>{amount}</td></tr>"
            html_content += "</table>"

            msg = MIMEText(html_content, "html")
            msg['Subject'] = 'KRC-20 Token 监控通知'
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL

            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SENDER_EMAIL, EMAIL_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            return True

        except Exception as e:
            print(f"Email error: {e}")
            return False

# app.py
import streamlit as st
import time
from datetime import datetime
import pandas as pd
from scraper import TokenScraper
from email_handler import EmailHandler
from config import REFRESH_INTERVAL

def main():
    st.set_page_config(page_title="KRC-20 Token Monitor", page_icon="📊")
    st.title("KRC-20 Token Monitor")

    # Initialize session state
    if 'token_history' not in st.session_state:
        st.session_state.token_history = []
    if 'monitoring' not in st.session_state:
        st.session_state.monitoring = False
    if 'scraper' not in st.session_state:
        st.session_state.scraper = TokenScraper()

    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button('开始监控' if not st.session_state.monitoring else '停止监控'):
            st.session_state.monitoring = not st.session_state.monitoring
            if not st.session_state.monitoring:
                st.session_state.scraper.stop_driver()

    with col2:
        if st.button('清除历史'):
            st.session_state.token_history = []

    # Display current status
    st.write(f"监控状态: {'运行中' if st.session_state.monitoring else '已停止'}")

    # Create placeholder for live data
    token_data_container = st.empty()
    history_container = st.empty()

    while st.session_state.monitoring:
        try:
            # Scrape token data
            token_data = st.session_state.scraper.scrape_tokens()
            
            if token_data:
                # Update current data display
                df_current = pd.DataFrame(
                    [[k, v] for k, v in token_data.items()],
                    columns=['Token', '数量']
                )
                token_data_container.dataframe(df_current, use_container_width=True)

                # Add to history with timestamp
                st.session_state.token_history.append({
                    'timestamp': datetime.now(),
                    'data': token_data
                })

                # Send email notification
                EmailHandler.send_email(token_data)

                # Display history
                if st.session_state.token_history:
                    history_df = pd.DataFrame([
                        {
                            'Time': h['timestamp'],
                            'Token': token,
                            'Amount': h['data'].get(token)
                        }
                        for h in st.session_state.token_history
                        for token in h['data'].keys()
                    ])
                    history_container.dataframe(
                        history_df.sort_values('Time', ascending=False),
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
            time.sleep(5)  # Wait before retrying
            continue

        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()