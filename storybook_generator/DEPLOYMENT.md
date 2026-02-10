# 部署指南

## 本地开发部署

参见主README.md的"快速开始"部分。

---

## 生产环境部署

### 使用Docker部署（推荐）

#### 1. 创建Dockerfile - 后端

创建 `backend/Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建存储目录
RUN mkdir -p storage/images storage/exports

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 创建Dockerfile - 前端

创建 `frontend/Dockerfile`：

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 3. 创建nginx配置

创建 `frontend/nginx.conf`：

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 代理API请求
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /storage {
        proxy_pass http://backend:8000;
    }
}
```

#### 4. 创建docker-compose.yml

项目根目录创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: storybook-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./storybook.db
      - DIFY_API_KEY=${DIFY_API_KEY}
      - DIFY_BASE_URL=${DIFY_BASE_URL}
      - DIFY_WORKFLOW_STAGE1=${DIFY_WORKFLOW_STAGE1}
      - DIFY_WORKFLOW_STAGE2=${DIFY_WORKFLOW_STAGE2}
      - DIFY_WORKFLOW_IMAGE_SELECTOR=${DIFY_WORKFLOW_IMAGE_SELECTOR}
      - JIMENG_API_KEY=${JIMENG_API_KEY}
      - JIMENG_BASE_URL=${JIMENG_BASE_URL}
    volumes:
      - ./backend/storage:/app/storage
      - ./backend/storybook.db:/app/storybook.db
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: storybook-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

#### 5. 部署

```bash
# 创建 .env 文件
cp backend/.env.example .env
# 编辑 .env 填入配置

# 构建和启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

访问 http://localhost

---

### 云服务器部署（传统方式）

#### 使用Nginx + Gunicorn

##### 1. 服务器准备（Ubuntu 20.04）

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3.9 python3.9-venv python3-pip nginx nodejs npm git

# 安装Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

##### 2. 部署后端

```bash
# 克隆代码
cd /var/www
sudo git clone <your-repo> storybook-generator
cd storybook-generator/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 配置环境变量
sudo nano .env
# 填入所有配置

# 测试运行
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

##### 3. 创建systemd服务

创建 `/etc/systemd/system/storybook-backend.service`：

```ini
[Unit]
Description=Storybook Generator Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/storybook-generator/backend
Environment="PATH=/var/www/storybook-generator/backend/venv/bin"
ExecStart=/var/www/storybook-generator/backend/venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/storybook-backend/access.log \
    --error-logfile /var/log/storybook-backend/error.log \
    main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 创建日志目录
sudo mkdir -p /var/log/storybook-backend
sudo chown www-data:www-data /var/log/storybook-backend

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable storybook-backend
sudo systemctl start storybook-backend
sudo systemctl status storybook-backend
```

##### 4. 部署前端

```bash
cd /var/www/storybook-generator/frontend

# 安装依赖
npm install

# 构建
npm run build

# 部署到nginx目录
sudo cp -r dist /var/www/storybook-frontend
```

##### 5. 配置Nginx

创建 `/etc/nginx/sites-available/storybook`：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名

    # 前端
    location / {
        root /var/www/storybook-frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件
    location /storage {
        proxy_pass http://127.0.0.1:8000;
    }

    # 日志
    access_log /var/log/nginx/storybook-access.log;
    error_log /var/log/nginx/storybook-error.log;
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/storybook /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启nginx
sudo systemctl restart nginx
```

##### 6. 配置SSL（可选但推荐）

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 证书会自动续期
```

---

### 环境变量配置

生产环境需要配置的关键环境变量：

```bash
# Dify配置（必需）
DIFY_API_KEY=your_production_api_key
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_WORKFLOW_STAGE1=workflow_id_1
DIFY_WORKFLOW_STAGE2=workflow_id_2
DIFY_WORKFLOW_IMAGE_SELECTOR=workflow_id_3

# 生图平台配置（至少配置一个）
JIMENG_API_KEY=your_jimeng_key
VOLCANO_API_KEY=your_volcano_key
MJ_API_KEY=your_mj_key

# 数据库（生产建议使用PostgreSQL）
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/storybook

# 安全配置
DEBUG=False
CORS_ORIGINS=https://your-domain.com

# 文件存储（可选使用对象存储）
STORAGE_PATH=/var/www/storybook-storage
```

---

### 性能优化

#### 1. 数据库优化

使用PostgreSQL替代SQLite：

```bash
# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres psql
CREATE DATABASE storybook;
CREATE USER storybook_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE storybook TO storybook_user;
\q

# 更新环境变量
DATABASE_URL=postgresql+asyncpg://storybook_user:strong_password@localhost/storybook
```

#### 2. 使用Redis缓存（可选）

```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

在代码中添加Redis缓存层。

#### 3. CDN加速

将生成的图片上传到CDN或对象存储（如阿里云OSS、AWS S3）。

---

### 监控和日志

#### 1. 日志管理

```bash
# 查看后端日志
sudo journalctl -u storybook-backend -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/storybook-access.log
```

#### 2. 监控工具

推荐使用：
- **Prometheus + Grafana**：系统监控
- **Sentry**：错误追踪
- **Uptime Robot**：服务可用性监控

---

### 备份策略

#### 1. 数据库备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/storybook"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U storybook_user storybook > $BACKUP_DIR/db_$DATE.sql

# 备份存储文件
tar -czf $BACKUP_DIR/storage_$DATE.tar.gz /var/www/storybook-storage

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

添加到crontab：

```bash
# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

---

### 安全建议

1. **防火墙**：只开放必要端口（80, 443）
2. **定期更新**：及时更新系统和依赖包
3. **密钥管理**：使用环境变量，不要硬编码
4. **HTTPS**：生产环境必须启用SSL
5. **限流**：使用Nginx限流防止滥用
6. **权限控制**：考虑添加用户认证系统

---

### 故障排查

#### 后端无法启动
```bash
# 检查服务状态
sudo systemctl status storybook-backend

# 查看详细日志
sudo journalctl -u storybook-backend -n 100
```

#### 前端无法访问
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 测试配置
sudo nginx -t
```

#### 数据库连接失败
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 测试连接
psql -U storybook_user -d storybook -h localhost
```

---

### 扩展性考虑

当业务增长时，可以考虑：

1. **负载均衡**：多个后端实例 + Nginx负载均衡
2. **容器编排**：使用Kubernetes管理Docker容器
3. **消息队列**：使用Celery + Redis处理异步任务
4. **微服务化**：拆分成独立的服务（生图服务、提示词服务等）

---

有问题请参考主README或提交Issue。
