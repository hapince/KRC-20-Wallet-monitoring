import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.text import MIMEText

# 定义发送邮件的函数
def send_email(content):
    sender_email = "your_email@gmail.com"
    receiver_email = "recipient_email@gmail.com"
    password = "your_app_password"

    msg = MIMEText(content)
    msg['Subject'] = 'Token Information'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.send_message(msg)

# 设置 Streamlit 输入
wallet_address = st.text_input("输入钱包地址:")
if st.button("抓取并发送邮件"):
    # 设置 Chrome 无头模式
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 初始化 WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # 访问指定钱包地址页面
        driver.get(f"https://kasplex.org/Currency?address={wallet_address}")

        # 抓取 token 信息
        table = driver.find_element("class name", "ant-table-body")  # 选择表格元素
        tokens_info = table.get_attribute('innerHTML')  # 获取表格的 HTML 内容

        # 发送邮件
        send_email(tokens_info)
        st.success("邮件已发送!")

    except Exception as e:
        st.error(f"发生错误: {e}")
    finally:
        driver.quit()
