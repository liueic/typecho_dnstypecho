# Typecho 灾备转移工具

## 简介

DNS自动切换工具是一个用于监控Typecho网站健康状态并在检测到异常时自动将DNS记录切换到备用服务器的自动化工具。当主站点服务不可用时，该工具会自动将域名解析指向备用IP地址，确保服务持续可用，并通过邮件通知管理员。

## 功能特点

- 自动监控网站健康状态
- 多次重试机制，避免因网络抖动导致误判
- 自动切换DNS记录到备用IP
- 邮件通知功能，及时通报状态变更
- 完全基于环境变量配置，便于部署
- 支持Docker容器化部署

![](https://s3.juniortree.com/pic/2025/06/0bfc6c6e2fe8b574772303af7a6c4ee2.webp)

![](https://s3.juniortree.com/pic/2025/06/f2dbe6fa42031d0deb40ca6fa54b09c8.webp)

![](https://s3.juniortree.com/pic/2025/06/f4cd3ab7651c9618e0c3ecaf0d334784.webp)

## 安装部署

- Docker 环境
- 阿里云账号及DNS管理权限
- SMTP邮件服务器

### docker compose 部署（推荐）

将.env.example文件复制为.env，并填写相应的配置：

```bash
cp .env.example .env
```

编辑.env文件，填写以下必要参数：

```
# 阿里云账号凭证
ALIBABA_CLOUD_ACCESS_KEY_ID=您的阿里云AccessKey
ALIBABA_CLOUD_ACCESS_KEY_SECRET=您的阿里云SecretKey

# SMTP邮件服务器配置
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password

# 域名配置
ADMIN_EMAIL=admin@example.com
DOMAIN_NAME=example.com
SUB_DOMAIN=www
RECORD_TYPE=A
BACKUP_IP=192.0.2.1

# 健康检查配置
HEALTH_PATH=/health.php
HEALTH_CHECK_MAX_RETRIES=3
HEALTH_CHECK_RETRY_INTERVAL=5
HEALTH_CHECK_TIMEOUT=5
```

克隆代码仓库或创建以下文件：

docker-compose：

```
services:
  dns_change:
    image: ghcr.io/liueic/typecho_dnstypecho-dns-failover:latest
    container_name: dns_change
    restart: always
    env_file:
      - .env
    command: >
      sh -c "env > /tmp/env.txt && cat /tmp/env.txt && exec docker-entrypoint.sh"
```

确保 `.env`文件和docker-compose文件在同一文件夹内

## 本地开发

本项目使uv包管理器

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

克隆项目并创建虚拟环境

```bash
uv venv
source .venv/bin/activate
```

安装依赖

```bash
uv pip install -r requirements.txt
```

配置环境变量

```bash
cp .env.example .env
```

运行

```bash
python3 main.py
```