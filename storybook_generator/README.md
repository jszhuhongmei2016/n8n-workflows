# 动态绘本自动生成图片系统

基于AI的动态绘本创作工具，集成Dify工作流和多个AI生图平台，实现从文本到图像的自动化绘本创作。

## ✨ 核心功能

### 🎨 智能提示词生成
- **阶段一**：自动分析绘本内容，生成人物、场景、道具的参考图提示词
- **阶段二**：为每页生成完整的10模块提示词（风格、人物、场景、构图等）
- 基于Dify工作流，提示词质量稳定且符合规范

### 🖼️ 多平台AI生图
- 支持**即梦**、**火山引擎**、**Midjourney**等多个生图平台
- 可配置图片尺寸（16:9、1:1等）和分辨率（2K、4K）
- 支持风格参考图上传和反推提示词

### 🤖 AI智能选图
- 集成Gemini自动评分和选择最佳生成结果
- 支持人工复选和单张重新生成
- 在线预览、放大查看

### 📊 批量管理
- Excel批量导出/导入提示词
- 批量生成参考图和页面图片
- 批量下载PNG格式图片

## 🏗️ 技术架构

```
┌─────────────┐
│   前端 Web   │  React + Vite + TailwindCSS
└──────┬──────┘
       │ HTTP
┌──────▼──────┐
│  后端 API    │  Python FastAPI + SQLAlchemy
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌─▼─────┐
│Dify │ │生图API │
│工作流│ │即梦等  │
└─────┘ └───────┘
```

### 后端技术栈
- **Web框架**: FastAPI
- **数据库**: SQLite（异步）+ SQLAlchemy
- **AI集成**: Dify工作流 + Gemini
- **生图平台**: 即梦/火山引擎/Midjourney API
- **文件处理**: openpyxl, Pillow

### 前端技术栈
- **框架**: React 18 + Vite
- **样式**: TailwindCSS
- **路由**: React Router
- **HTTP**: Axios
- **UI**: React Icons, React Hot Toast

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+
- Dify账号（需要创建工作流）
- 生图平台API密钥（即梦/火山引擎等）

### 1. 克隆项目

```bash
cd storybook_generator
```

### 2. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 文件，填入API密钥
```

**必需配置项**：
- `DIFY_API_KEY`: Dify API密钥
- `DIFY_WORKFLOW_STAGE1`: 阶段一工作流ID
- `DIFY_WORKFLOW_STAGE2`: 阶段二工作流ID
- `DIFY_WORKFLOW_IMAGE_SELECTOR`: 图片选择工作流ID
- `JIMENG_API_KEY`: 即梦API密钥（或其他平台）

### 3. 启动后端

```bash
python main.py
```

后端运行在: http://localhost:8000  
API文档: http://localhost:8000/docs

### 4. 配置前端

```bash
cd ../frontend

# 安装依赖
npm install
# 或使用 yarn/pnpm

# 可选：配置环境变量
# 创建 .env 文件
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
```

### 5. 启动前端

```bash
npm run dev
```

前端运行在: http://localhost:3000

## 📖 使用流程

### 步骤1：创建项目
1. 输入项目名称
2. 选择目标年龄段（如7-9岁）
3. 选择图片尺寸（16:9、1:1等）和分辨率
4. 选择生图平台（即梦/火山引擎/MJ）

### 步骤2：选择风格
- 从内置风格库选择
- 或上传风格参考图自动反推提示词
- 或自定义风格描述

### 步骤3：上传绘本内容
上传文本文件，格式：
```
P1
这是第一页的内容...

P2
这是第二页的内容...
```

### 步骤4：生成参考图提示词
- AI自动分析内容，识别人物、场景、道具
- 生成符合规范的参考图提示词
- 可手动编辑和调整

### 步骤5：生成参考图
- 批量生成所有参考图
- 查看和确认生成结果
- 不满意可重新生成

### 步骤6：规划页面
- 为每页选择要使用的参考图
  - 人物：最多3个
  - 非人物角色：最多2个
  - 场景：最多1个

### 步骤7：生成页面提示词
- AI自动组装完整的10模块提示词
- 可导出Excel批量编辑
- 上传修改后的Excel替换

### 步骤8：生成图片
- 批量生成所有页面图片（每页3张）
- AI自动评分选择最佳
- 可人工复选或重新生成

### 步骤9：下载导出
- 单张/批量下载PNG图片
- 导出提示词Excel
- 导出项目数据

## 📂 项目结构

```
storybook_generator/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 服务层（Dify、生图API）
│   │   └── utils/       # 工具函数
│   ├── storage/         # 文件存储
│   ├── main.py          # 主应用
│   └── requirements.txt # Python依赖
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── api/        # API调用
│   │   ├── components/ # 组件
│   │   ├── pages/      # 页面
│   │   └── App.jsx     # 主应用
│   └── package.json    # Node依赖
└── README.md           # 本文件
```

## 🔧 Dify工作流配置

需要在Dify中创建3个工作流：

### 工作流1：阶段一参考图提示词生成器
**输入**：
- `storybook_content`: 绘本完整内容
- `style_prompt`: 风格提示词
- `target_age`: 目标年龄段

**输出**：
```json
{
  "characters": [{"name": "小明", "prompt": "..."}],
  "non_characters": [{"name": "书包", "prompt": "..."}],
  "scenes": [{"name": "教室", "prompt": "..."}]
}
```

### 工作流2：阶段二页面提示词生成器
**输入**：
- `page_number`: 页码（P1）
- `page_content`: 页面文本
- `scene_type`: 画面类型
- `style_prompt`: 风格提示词
- `reference_images`: 引用的参考图

**输出**：
```json
{
  "prompt": "完整提示词...",
  "modules": {...}
}
```

### 工作流3：图片评选器
**输入**：
- `images`: 图片URL列表
- `page_content`: 页面内容
- `prompt`: 生成提示词

**输出**：
```json
{
  "selected_index": 0,
  "scores": [85, 90, 78],
  "reasons": ["...", "...", "..."]
}
```

## 📝 API文档

启动后端后访问 http://localhost:8000/docs 查看完整的API文档（Swagger UI）。

主要端点：
- `/api/projects/` - 项目管理
- `/api/reference-images/` - 参考图管理
- `/api/pages/` - 页面管理
- `/api/images/` - 图片生成
- `/api/exports/` - 导出下载

## ⚠️ 注意事项

1. **API密钥安全**：不要将包含真实密钥的 `.env` 文件提交到版本控制
2. **存储空间**：生成的图片会占用较多空间，建议定期清理
3. **生图成本**：注意各平台的API调用计费
4. **网络稳定**：生图过程需要稳定的网络连接
5. **Dify工作流**：确保Dify工作流已正确配置并测试通过

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Dify文档](https://docs.dify.ai/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [React文档](https://react.dev/)
- [即梦API文档](需根据实际平台)

---

**祝你创作愉快！** 🎨✨
