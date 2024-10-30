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
import tkinter as tk
from tkinter import scrolledtext
import threading

# Tkinter UI setup
root = tk.Tk()
root.title("TRC20 钱包监控")

tk.Label(root, text="指定地址:").grid(row=0, column=0)
address_entry = tk.Entry(root, width=50)
address_entry.grid(row=0, column=1)

tk.Label(root, text="接收邮箱:").grid(row=1, column=0)
receiver_email_entry = tk.Entry(root, width=50)
receiver_email_entry.grid(row=1, column=1)

output_text = scrolledtext.ScrolledText(root, width=70, height=20)
output_text.grid(row=3, columnspan=2)

smtp_server = "smtp.gmail.com"
smtp_port = 465
sender_email = "happy.prince.max@gmail.com" #填自己的邮箱 
password = "******"    #去谷歌申请一个密码

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# 启动Chrome浏览器
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def send_email(token_data, receiver_email):
    try:
        html_content = "<h2>KRC-20 Token 监控通知</h2><table border='1'><tr><th>Token 名称</th><th>数量</th></tr>"
        for token, amount in token_data.items():
            html_content += f"<tr><td>{token}</td><td>{amount}</td></tr>"
        html_content += "</table>"

        msg = MIMEText(html_content, "html")
        msg['Subject'] = 'KRC-20 Token 监控通知'
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"发送邮件时出错: {e}")

def scrape_tokens(address, receiver_email):
    url = f"https://kasplex.org/Currency?address={address}"
    driver.get(url)

    try: 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ant-table-tbody'))
        )
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tokens_table_body = soup.find('tbody', class_='ant-table-tbody')

        if tokens_table_body:
            token_data = {}
            for row in tokens_table_body.find_all('tr', class_='ant-table-row ant-table-row-level-0'):
                token_name_with_span = row.find('td', class_='ant-table-cell searchCell').get_text(strip=True)
                token_name = token_name_with_span.split('Fair Mint')[0].strip()
                token_amount_str = row.find_all('td', class_='ant-table-cell deployTime')[1].get_text(strip=True)

                # 调试信息，打印原始抓取的数量
                print(f"原始数量: {token_amount_str}")

                # 去掉非数字字符
                token_amount_str = ''.join(filter(str.isdigit, token_amount_str))

                # 转换数量并减去 7 个零
                try:
                    if token_amount_str:  # 确保字符串不为空
                        token_amount = int(token_amount_str) / 10**8
                    else:
                        token_amount = 0  # 如果没有有效的数量，设置为 0
                except ValueError:
                    token_amount = token_amount_str  # 如果转换失败，保留原字符串

                # 调试信息，打印处理后的数量
                print(f"处理后的数量: {token_amount}")

                token_data[token_name] = token_amount
            send_email(token_data, receiver_email)
            output_text.insert(tk.END, f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 抓取的铭文: {token_data}\n")
            output_text.yview(tk.END)

        else:
            print("没找到")
            output_text.insert(tk.END, "没找到\n")

    except Exception as e:
        print(f"发生错误: {e}")

def start_monitoring():
    address = address_entry.get()
    receiver_email = receiver_email_entry.get()
    
    # 运行抓取过程
    while True:
        scrape_tokens(address, receiver_email)
        time.sleep(60)

def submit():
    # 创建一个新线程来执行抓取
    thread = threading.Thread(target=start_monitoring, daemon=True)
    thread.start()

# 添加提交按钮
submit_button = tk.Button(root, text="提交", command=submit)
submit_button.grid(row=2, columnspan=2)

root.mainloop()

# Clean up
driver.quit()
