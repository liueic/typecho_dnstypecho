FROM python:3.13-slim

# 安装 curl、cron、unzip 和 procps(提供ps命令)
RUN apt-get update && apt-get install -y curl unzip cron procps

WORKDIR /app

# 拷贝项目代码
COPY . /app

# 安装 Python 依赖
RUN pip install -r requirements.txt

# 拷贝 crontab 文件
COPY crontab /etc/cron.d/health_cron

# 设置权限
RUN chmod 0644 /etc/cron.d/health_cron && \
    echo "" >> /etc/cron.d/health_cron && \
    crontab /etc/cron.d/health_cron

# 创建日志目录和日志文件
RUN mkdir -p /var/log/cron && \
    touch /var/log/cron/cron.log && \
    chmod 0644 /var/log/cron/cron.log

# 拷贝 docker-entrypoint.sh 脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 设置容器启动时执行的命令
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]