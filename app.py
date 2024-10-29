import time
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import streamlit as st

# 邮件发送配置
smtp_server = "smtp.gmail.com"
smtp_port = 465
sender_email = "happy.prince.max@gmail.com"  # 发送方邮箱
receiver_email = "17300766401@163.com"  # 接收方邮箱
password = "unpn umpg hvzg elxe"  # 应用专用密码

# 设置无头模式
options = Options()
options.add_argument("--headless")  # 启用无头模式
options.add_argument("--disable-gpu")  # 禁用 GPU 硬件加速
options.add_argument("--no-sandbox")  # 解决 DevToolsActivePort 文件不存在的报错

# 启动Chrome浏览器
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def send_email(token_data):
    try:
        # 构造邮件内容
        html_content = "<h2>KRC-20 Token 监控通知</h2><table border='1'><tr><th>Token 名称</th><th>数量</th></tr>"
        for token, amount in token_data.items():
            html_content += f"<tr><td>{token}</td><td>{amount}</td></tr>"
        html_content += "</table>"

        msg = MIMEText(html_content, "html")  # 发送 HTML 格式的邮件
        msg['Subject'] = 'KRC-20 Token 监控通知'
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        st.success("邮件发送成功")  # 邮件发送成功的提示
    except Exception as e:
        st.error(f"发送邮件时出错: {e}")  # 输出错误信息

def scrape_tokens(wallet_address):
    url = f"https://kasplex.org/Currency?address={wallet_address}"  # 构建监控地址
    driver.get(url)

    try:
        # 等待表格的主体加载，最大等待时间为10秒
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ant-table-tbody'))
        )

        # 继续等待直到表格内容填充
        time.sleep(3)  # 确保动态内容加载完成

        # 获取页面内容
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 找到表格主体
        tokens_table_body = soup.find('tbody', class_='ant-table-tbody')

        if tokens_table_body:
            token_data = {}
            # 遍历每个tr
            for row in tokens_table_body.find_all('tr', class_='ant-table-row ant-table-row-level-0'):
                # 获取Token名称并去掉<span>标签中的内容
                token_name_with_span = row.find('td', class_='ant-table-cell searchCell').get_text(strip=True)
                token_name = token_name_with_span.split('Fair Mint')[0].strip()  # 只取 'tick' 中的内容
                token_amount = row.find_all('td', class_='ant-table-cell deployTime')[1].get_text(strip=True)
                token_data[token_name] = token_amount
            
            # 发送邮件通知
            send_email(token_data)
            st.write(f"当前抓取的Token: {token_data}")  # 输出当前抓取的Token
            
        else:
            st.warning("未找到Token表格主体")

    except Exception as e:
        st.error(f"发生错误: {e}")  # 输出错误信息

# Streamlit 应用主界面
st.title("KRC-20 Token 监控")
wallet_address = st.text_input("输入要监控的钱包地址", "kaspa:qr5ersqcxrpphkz24k389c9ewtfeh007naglgfjztzr9rpgwv4gd52jj2dzfv")

if st.button("开始监控"):
    with st.spinner("正在抓取数据..."):
        scrape_tokens(wallet_address)
        time.sleep(60)  # 每60秒检查一次

# 清理资源
driver.quit()
