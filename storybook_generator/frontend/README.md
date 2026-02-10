# Storybook Generator - Frontend

动态绘本自动生成图片系统的前端应用。

## 技术栈

- **框架**: React 18
- **构建工具**: Vite
- **路由**: React Router
- **样式**: TailwindCSS
- **HTTP客户端**: Axios
- **状态管理**: Zustand (可选)
- **UI组件**: React Icons, React Hot Toast

## 安装

```bash
# 安装依赖
npm install
# 或
yarn install
# 或
pnpm install
```

## 开发

```bash
# 启动开发服务器
npm run dev
```

访问: http://localhost:3000

## 构建

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API调用
│   ├── components/       # 可复用组件
│   ├── pages/            # 页面组件
│   ├── stores/           # 状态管理
│   ├── utils/            # 工具函数
│   ├── App.jsx           # 主应用
│   ├── main.jsx          # 入口文件
│   └── index.css         # 全局样式
├── public/               # 静态资源
├── index.html            # HTML模板
├── vite.config.js        # Vite配置
├── tailwind.config.js    # Tailwind配置
└── package.json
```

## 页面路由

- `/` - 首页
- `/projects` - 项目列表
- `/projects/:id` - 项目详情
- `/projects/:id/stage1` - 阶段一：参考图生成
- `/projects/:id/stage2` - 阶段二：页面提示词生成
- `/projects/:id/generation` - 图片生成与选择

## 环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 开发说明

1. 前端通过Vite代理连接后端API（配置在vite.config.js）
2. 所有API请求已封装在 `src/api/index.js`
3. 使用Tailwind CSS进行样式开发
4. 组件采用函数式组件 + Hooks

## 注意事项

- 确保后端服务运行在 http://localhost:8000
- 开发时热更新会自动刷新页面
- 生产构建产物在 `dist/` 目录
