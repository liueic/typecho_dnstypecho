import os
import sys
from dotenv import load_dotenv
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time  # 添加time模块用于重试间隔

from typing import List
import logging
from datetime import datetime
import socket

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

logging.basicConfig(level=logging.WARNING)

load_dotenv()

class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Alidns20150109Client:
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
        )
        config.endpoint = 'alidns.cn-shanghai.aliyuncs.com'
        return Alidns20150109Client(config)

    @staticmethod
    def get_record_id(domain_name: str, rrkey_word: str, type_key_word: str) -> str:
        """
        查询指定域名、主机记录和记录类型的第一个 recordId
        """
        client = Sample.create_client()
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name=domain_name,
            rrkey_word=rrkey_word,
            type_key_word=type_key_word
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = client.describe_domain_records_with_options(describe_domain_records_request, runtime)
            data = response.to_map() if hasattr(response, "to_map") else response
            records = data.get("body", {}).get("DomainRecords", {}).get("Record", [])
            if records:
                return records[0].get("RecordId")
            else:
                return None
        except Exception as error:
            print(f"Error: {error}")
            return None
        
    @staticmethod
    def change_dns(record: str, rr: str, type: str, value: str) -> None:
        """
        修改指定记录的值
        """
        client = Sample.create_client()
        update_domain_record_request = alidns_20150109_models.UpdateDomainRecordRequest(
            record_id=record,
            type=type,
            rr=rr,
            value=value
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = client.update_domain_record_with_options(update_domain_record_request, runtime)
            print(f"Change DNS Response: {response.to_map() if hasattr(response, 'to_map') else response}")
        except Exception as error:
            print(f"Error: {error}")

    @staticmethod
    def get_health_status(health_endpoint: str) -> bool:
        """
        获取健康检查状态，包含重试机制
        """
        admin_email = os.getenv("ADMIN_EMAIL")
        # 从环境变量获取重试配置
        max_retries = int(os.getenv("HEALTH_CHECK_MAX_RETRIES", 3))
        retry_interval = int(os.getenv("HEALTH_CHECK_RETRY_INTERVAL", 5))
        timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", 5))
        
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                logging.info(f"执行健康检查 (尝试 {retry_count + 1}/{max_retries})...")
                response = requests.get(health_endpoint, timeout=timeout)
                data = response.json()
                
                if data.get("overall") == 'healthy':
                    if retry_count > 0:
                        logging.info(f"健康检查成功，之前失败 {retry_count} 次")
                    return True
                else:
                    logging.warning(f"健康检查返回非健康状态: {data}")
                    last_error = f"服务返回非健康状态: {data}"
            except requests.RequestException as e:
                error_body = ""
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_body = e.response.text
                    except Exception:
                        error_body = str(e)
                else:
                    error_body = str(e)
                
                logging.warning(f"健康检查失败 (尝试 {retry_count + 1}/{max_retries}): {error_body}")
                last_error = error_body
            
            retry_count += 1
            if retry_count < max_retries:
                logging.info(f"等待 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
        
        # 所有重试都失败后发送邮件通知
        logging.error(f"健康检查在 {max_retries} 次尝试后失败: {last_error}")
        Sample.send_email(
            subject="健康检查接口异常",
            body=f"健康检查接口在 {max_retries} 次尝试后仍然失败：\n\n最后错误: {last_error}\n时间：{datetime.now()}\n主机：{socket.gethostname()}",
            to_email=admin_email
        )
        return False

    @staticmethod
    def send_email(subject: str, body: str, to_email: str) -> None:
        """
        发送电子邮件
        """
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 465))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        try:
            print(f"Connecting to SMTP server {smtp_server}:{smtp_port} with SSL")
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
                print("Logging in...")
                server.login(smtp_user, smtp_password)
                print("Logged in, sending email...")
                # 使用MIMEText构造邮件
                msg = MIMEText(body, 'plain', 'utf-8')
                msg['Subject'] = Header(subject, 'utf-8')
                msg['From'] = smtp_user
                msg['To'] = to_email
                server.sendmail(smtp_user, [to_email], msg.as_string())
            print("Email sent successfully.")
        except Exception as e:
            print(f"Failed to send email: {e}")

if __name__ == '__main__':
    # 校验环境变量
    required_envs = [
        "ALIBABA_CLOUD_ACCESS_KEY_ID",
        "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
        "SMTP_SERVER",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "ADMIN_EMAIL",
        "DOMAIN_NAME",
        "BACKUP_IP",
    ]
    for env in required_envs:
        if not os.getenv(env):
            logging.error(f"环境变量 {env} 未设置，程序退出。")
            sys.exit(1)

    # 添加新的环境变量
    domain_name = os.getenv("DOMAIN_NAME")
    sub_domain = os.getenv("SUB_DOMAIN", "www")
    record_type = os.getenv("RECORD_TYPE", "A")
    backup_ip = os.getenv("BACKUP_IP")
    health_path = os.getenv("HEALTH_PATH", "/health.php")
    admin_email = os.getenv("ADMIN_EMAIL")

    # 使用环境变量构建健康检查URL
    health_endpoint = f'https://{sub_domain}.{domain_name}{health_path}'
    health_status = Sample.get_health_status(health_endpoint)

    if health_status:
        logging.info("Health check passed.")
    else:
        logging.warning("Health check failed.")
        record_id = Sample.get_record_id(domain_name, sub_domain, record_type)
        logging.info(f"RecordId: {record_id}")
        if record_id:
            try:
                Sample.change_dns(record_id, sub_domain, record_type, backup_ip)
                Sample.send_email(
                    subject="DNS切换成功通知",
                    body=f"博客服务健康检查失败，已自动将DNS切换至备用服务器。\n\n详细信息：\n- 域名记录：{sub_domain}.{domain_name}\n- 目标IP：{backup_ip}\n- 时间：{datetime.now()}\n- 主机：{socket.gethostname()}",
                    to_email=admin_email
                )
            except Exception as e:
                error_info = f"DNS切换异常：{str(e)}"
                Sample.send_email(
                    subject="博客服务异常",
                    body=f"博客服务出现异常，请尽快处理。\n\n异常信息：{error_info}\n时间：{datetime.now()}\n主机：{socket.gethostname()}",
                    to_email=admin_email
                )
        else:
            Sample.send_email(
                subject="DNS记录未找到",
                body=f"未找到 {sub_domain}.{domain_name} 的{record_type}记录，无法切换DNS。\n时间：{datetime.now()}\n主机：{socket.gethostname()}",
                to_email=admin_email
            )