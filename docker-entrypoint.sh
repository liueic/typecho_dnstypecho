#!/bin/bash
set -e

# 保存环境变量到文件，供cron任务使用
env | grep -v "^_=" > /etc/environment

# 确保日志文件存在
mkdir -p /var/log/cron
touch /var/log/cron/cron.log
chmod 0644 /var/log/cron/cron.log

# 使用service命令启动cron
service cron start

# 查看crontab是否正确配置
crontab -l

# 保持容器运行
tail -f /var/log/cron/cron.log