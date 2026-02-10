# Storybook Generator - Backend

动态绘本自动生成图片系统的后端服务。

## 技术栈

- **Web框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy (异步)
- **AI工作流**: Dify
- **生图平台**: 即梦/火山引擎/Midjourney
- **文件处理**: openpyxl, Pillow

## 安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

必需配置：
- `DIFY_API_KEY`: Dify API密钥
- `DIFY_WORKFLOW_STAGE1`: 阶段一工作流ID（生成参考图提示词）
- `DIFY_WORKFLOW_STAGE2`: 阶段二工作流ID（生成页面提示词）
- `DIFY_WORKFLOW_IMAGE_SELECTOR`: 图片选择工作流ID
- `JIMENG_API_KEY`: 即梦API密钥（或其他生图平台）

## 运行

```bash
# 开发模式（自动重载）
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问: http://localhost:8000

API文档: http://localhost:8000/docs

## API概览

### 项目管理
- `POST /api/projects/` - 创建项目
- `GET /api/projects/` - 获取项目列表
- `GET /api/projects/{id}` - 获取项目详情
- `PUT /api/projects/{id}` - 更新项目
- `POST /api/projects/{id}/upload-content` - 上传绘本内容
- `POST /api/projects/{id}/upload-style-reference` - 上传风格参考图

### 参考图（阶段一）
- `POST /api/reference-images/projects/{id}/generate-prompts` - 生成参考图提示词
- `GET /api/reference-images/projects/{id}/references` - 获取参考图列表
- `POST /api/reference-images/{id}/generate` - 生成参考图
- `POST /api/reference-images/{id}/check-status` - 检查生成状态

### 页面（阶段二）
- `POST /api/pages/projects/{id}/plan-pages` - 规划页面
- `POST /api/pages/{id}/generate-prompt` - 生成页面提示词
- `POST /api/pages/projects/{id}/generate-all-prompts` - 批量生成提示词

### 图片生成
- `POST /api/images/pages/{id}/generate` - 生成页面图片
- `POST /api/images/{id}/check-status` - 检查生成状态
- `POST /api/images/pages/{id}/auto-select` - AI自动选图
- `POST /api/images/{id}/select` - 用户选择图片

### 导出
- `GET /api/exports/projects/{id}/prompts/excel` - 导出提示词Excel
- `POST /api/exports/projects/{id}/prompts/import` - 导入提示词Excel
- `GET /api/exports/images/{id}/download` - 下载图片

## 项目结构

```
backend/
├── app/
│   ├── api/              # API路由
│   │   ├── projects.py
│   │   ├── reference_images.py
│   │   ├── pages.py
│   │   ├── images.py
│   │   └── exports.py
│   ├── models/           # 数据模型
│   │   ├── project.py
│   │   ├── reference_image.py
│   │   ├── page.py
│   │   └── generated_image.py
│   ├── services/         # 服务层
│   │   ├── dify_service.py
│   │   └── image_service.py
│   ├── utils/            # 工具函数
│   │   ├── file_utils.py
│   │   └── excel_utils.py
│   ├── config.py         # 配置
│   └── database.py       # 数据库
├── storage/              # 文件存储
│   ├── images/
│   └── exports/
├── main.py               # 主应用
├── requirements.txt      # 依赖
└── .env                  # 环境变量
```

## 开发

1. 数据库初始化会在首次运行时自动完成
2. 所有API都有详细的文档，访问 `/docs` 查看
3. 支持CORS，可配置允许的源
