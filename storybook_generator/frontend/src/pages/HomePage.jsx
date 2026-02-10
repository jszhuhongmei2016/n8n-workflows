import { Link } from 'react-router-dom'
import { FiPlus, FiBookOpen, FiZap } from 'react-icons/fi'

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* 欢迎区域 */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          欢迎使用动态绘本生成器
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AI驱动的绘本创作工具，让故事可视化更简单
        </p>
        <Link to="/projects" className="btn btn-primary text-lg px-8 py-3">
          <FiPlus className="inline mr-2" />
          创建新项目
        </Link>
      </div>

      {/* 功能介绍 */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FiBookOpen className="text-primary-600" size={32} />
          </div>
          <h3 className="text-xl font-semibold mb-2">智能提示词生成</h3>
          <p className="text-gray-600">
            基于Dify工作流，自动生成符合规范的绘本提示词
          </p>
        </div>

        <div className="card text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FiZap className="text-green-600" size={32} />
          </div>
          <h3 className="text-xl font-semibold mb-2">多平台生图</h3>
          <p className="text-gray-600">
            支持即梦、火山引擎、Midjourney等多个AI生图平台
          </p>
        </div>

        <div className="card text-center">
          <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FiBookOpen className="text-purple-600" size={32} />
          </div>
          <h3 className="text-xl font-semibold mb-2">AI智能选图</h3>
          <p className="text-gray-600">
            使用Gemini自动评选最佳效果，节省人工筛选时间
          </p>
        </div>
      </div>

      {/* 工作流程 */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-6">创作流程</h2>
        <div className="space-y-4">
          {[
            { step: 1, title: '项目配置', desc: '设置项目名称、风格、生图平台等' },
            { step: 2, title: '上传内容', desc: '上传绘本文本（P1、P2格式）' },
            { step: 3, title: '生成参考图', desc: '自动生成人物、场景等参考图' },
            { step: 4, title: '规划页面', desc: '为每页选择要使用的参考图' },
            { step: 5, title: '生成提示词', desc: '自动生成完整的绘本提示词' },
            { step: 6, title: '图片生成', desc: 'AI自动生成并选择最佳图片' },
            { step: 7, title: '导出下载', desc: '导出Excel提示词和PNG图片' },
          ].map((item) => (
            <div key={item.step} className="flex items-start gap-4">
              <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                {item.step}
              </div>
              <div>
                <h4 className="font-semibold text-lg">{item.title}</h4>
                <p className="text-gray-600">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
