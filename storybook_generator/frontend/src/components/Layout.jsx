import { Link, useLocation } from 'react-router-dom'
import { FiHome, FiFolder, FiSettings } from 'react-icons/fi'

export default function Layout({ children }) {
  const location = useLocation()

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <div className="min-h-screen flex">
      {/* 侧边栏 */}
      <aside className="w-64 bg-white border-r border-gray-200">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-primary-600">
            动态绘本生成器
          </h1>
        </div>
        
        <nav className="px-4 space-y-2">
          <Link
            to="/"
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              isActive('/') && location.pathname === '/'
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <FiHome size={20} />
            <span className="font-medium">首页</span>
          </Link>
          
          <Link
            to="/projects"
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              isActive('/projects')
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <FiFolder size={20} />
            <span className="font-medium">项目管理</span>
          </Link>
        </nav>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
