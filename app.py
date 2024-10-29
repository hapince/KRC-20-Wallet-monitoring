# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
DEFAULT_SENDER_EMAIL = "happy.prince.max@gmail.com"
DEFAULT_SENDER_PASSWORD = "unpn umpg hvzg elxe"

# Base URL
BASE_URL = "https://kasplex.org/Currency?address="
REFRESH_INTERVAL = 60  # seconds

# scraper.py
import asyncio
from typing import Dict
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from config import BASE_URL

class TokenScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def start_browser(self):
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

    async def stop_browser(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None

    async def scrape_tokens(self, wallet_address: str) -> Dict[str, str]:
        try:
            if not self.browser:
                await self.start_browser()

            url = f"{BASE_URL}{wallet_address}"
            await self.page.goto(url)
            await self.page.wait_for_selector('.ant-table-tbody')
            await asyncio.sleep(3)  # Wait for dynamic content

            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
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
from config import SMTP_SERVER, SMTP_PORT

class EmailHandler:
    @staticmethod
    def send_email(token_data: Dict[str, str], sender_email: str, sender_password: str, receiver_email: str) -> bool:
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
            msg['From'] = sender_email
            msg['To'] = receiver_email

            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
            return True

        except Exception as e:
            print(f"Email error: {e}")
            return False

# app.py
import streamlit as st
import asyncio
from datetime import datetime
import pandas as pd
from scraper import TokenScraper
from email_handler import EmailHandler
from config import REFRESH_INTERVAL, DEFAULT_SENDER_EMAIL, DEFAULT_SENDER_PASSWORD
import json

def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            'wallet_addresses': [],
            'receiver_email': '',
            'sender_email': DEFAULT_SENDER_EMAIL,
            'sender_password': DEFAULT_SENDER_PASSWORD
        }

def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

async def monitor_tokens(scraper, wallet_address, token_data_container, history_container, email_settings):
    try:
        token_data = await scraper.scrape_tokens(wallet_address)
        
        if token_data:
            # Update current data display
            current_time = datetime.now()
            df_current = pd.DataFrame(
                [[k, v, wallet_address, current_time] for k, v in token_data.items()],
                columns=['Token', '数量', '钱包地址', '时间']
            )
            token_data_container.dataframe(df_current, use_container_width=True)

            # Add to history
            if 'token_history' not in st.session_state:
                st.session_state.token_history = []
            
            st.session_state.token_history.extend([
                {
                    'timestamp': current_time,
                    'wallet': wallet_address,
                    'token': token,
                    'amount': amount
                }
                for token, amount in token_data.items()
            ])

            # Send email if configured
            if all(email_settings.values()):
                EmailHandler.send_email(
                    token_data,
                    email_settings['sender_email'],
                    email_settings['sender_password'],
                    email_settings['receiver_email']
                )

            # Display history
            if st.session_state.token_history:
                history_df = pd.DataFrame(st.session_state.token_history)
                history_df = history_df.sort_values('timestamp', ascending=False)
                history_container.dataframe(history_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error occurred: {str(e)}")

def main():
    st.set_page_config(page_title="KRC-20 Token Monitor", page_icon="📊", layout="wide")
    st.title("KRC-20 Token Monitor")

    # Load saved settings
    settings = load_settings()

    # Sidebar for settings
    with st.sidebar:
        st.header("监控设置")
        
        # Wallet management
        st.subheader("钱包地址管理")
        new_wallet = st.text_input("添加新钱包地址")
        if st.button("添加钱包"):
            if new_wallet and new_wallet not in settings['wallet_addresses']:
                settings['wallet_addresses'].append(new_wallet)
                save_settings(settings)

        # Display and allow removal of existing wallets
        for wallet in settings['wallet_addresses']:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(wallet)
            with col2:
                if st.button("删除", key=f"del_{wallet}"):
                    settings['wallet_addresses'].remove(wallet)
                    save_settings(settings)
                    st.experimental_rerun()

        # Email settings
        st.subheader("邮件设置")
        settings['receiver_email'] = st.text_input("接收邮箱", settings['receiver_email'])
        settings['sender_email'] = st.text_input("发送邮箱", settings['sender_email'])
        settings['sender_password'] = st.text_input("邮箱密码", settings['sender_password'], type="password")
        
        if st.button("保存设置"):
            save_settings(settings)
            st.success("设置已保存！")

    # Initialize session state
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
                asyncio.run(st.session_state.scraper.stop_browser())

    with col2:
        if st.button('清除历史'):
            st.session_state.token_history = []

    # Display current status
    st.write(f"监控状态: {'运行中' if st.session_state.monitoring else '已停止'}")

    # Create containers for data display
    token_data_container = st.empty()
    history_container = st.empty()

    # Monitor all configured wallets
    if st.session_state.monitoring and settings['wallet_addresses']:
        for wallet in settings['wallet_addresses']:
            asyncio.run(monitor_tokens(
                st.session_state.scraper,
                wallet,
                token_data_container,
                history_container,
                {
                    'sender_email': settings['sender_email'],
                    'sender_password': settings['sender_password'],
                    'receiver_email': settings['receiver_email']
                }
            ))
        st.experimental_rerun()

if __name__ == "__main__":
    main()

