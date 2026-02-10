# Dify工作流配置指南

本文档详细说明如何在Dify中创建三个核心工作流。

## 前置准备

1. 注册Dify账号：https://dify.ai/
2. 创建新的工作流（Workflow）
3. 获取API密钥

## 工作流1：阶段一参考图提示词生成器

### 功能
分析绘本内容，自动生成人物角色、非人物角色、场景的参考图提示词。

### 输入变量
```json
{
  "storybook_content": {
    "type": "string",
    "description": "绘本完整内容（P1、P2格式）",
    "required": true
  },
  "style_prompt": {
    "type": "string",
    "description": "整体风格提示词",
    "required": true
  },
  "target_age": {
    "type": "string",
    "description": "目标年龄段（如7-9岁）",
    "required": false,
    "default": "7-9岁"
  }
}
```

### 处理流程
1. **内容分析节点**（LLM）
   - 模型：GPT-4 或 Claude Sonnet
   - 提示词：
   ```
   你是资深绘本插画艺术师。请分析以下绘本内容，识别：
   1. 人物角色（姓名、年龄、特征）
   2. 非人物角色（重要道具、物品）
   3. 场景（地点、环境）
   
   绘本内容：
   {{storybook_content}}
   
   目标年龄：{{target_age}}
   
   以JSON格式输出：
   {
     "characters": [{"name": "角色名", "age": "年龄", "features": "特征"}],
     "non_characters": [{"name": "物品名", "type": "类型"}],
     "scenes": [{"name": "场景名", "type": "室内/室外"}]
   }
   ```

2. **生成人物提示词节点**（LLM）
   - 模型：GPT-4
   - 提示词：
   ```
   为每个人物角色生成完整的参考图提示词。
   
   整体风格：{{style_prompt}}
   
   角色信息：{{characters}}
   
   要求：
   1. 包含画风、身份、外形特征、动作姿态、气质
   2. 中性背景，全身，五官清晰
   3. 符合{{target_age}}儿童理解
   4. 不超过800字
   
   格式：
   人物角色1：[角色名]提示词
   [完整提示词内容]
   ```

3. **生成非人物提示词节点**（LLM）
   - 类似人物，但针对道具物品

4. **生成场景提示词节点**（LLM）
   - 生成纯场景描述（无人物）

5. **整合输出节点**（Code）
   ```python
   import json
   
   def main(characters_prompts, non_characters_prompts, scenes_prompts):
       return {
           "characters": parse_prompts(characters_prompts),
           "non_characters": parse_prompts(non_characters_prompts),
           "scenes": parse_prompts(scenes_prompts)
       }
   
   def parse_prompts(text):
       # 解析提示词文本为结构化数据
       result = []
       # ... 解析逻辑
       return result
   ```

### 输出格式
```json
{
  "characters": [
    {
      "name": "小明",
      "prompt": "以轻盈克制水彩为核心...[完整提示词]"
    }
  ],
  "non_characters": [
    {
      "name": "书包",
      "prompt": "以轻盈克制水彩为核心...[完整提示词]"
    }
  ],
  "scenes": [
    {
      "name": "教室一角",
      "prompt": "以轻盈克制水彩为核心...[完整提示词]"
    }
  ]
}
```

---

## 工作流2：阶段二页面提示词生成器

### 功能
为单个绘本页面生成完整的10模块提示词。

### 输入变量
```json
{
  "page_number": "P1",
  "page_content": "该页文本内容",
  "scene_type": "real_scene/knowledge/abstract",
  "style_prompt": "整体风格",
  "reference_images": {
    "characters": [...],
    "non_characters": [...],
    "scene": {...}
  },
  "target_age": "7-9岁"
}
```

### 处理流程
1. **场景分析节点**（LLM）
   - 分析页面内容，确定画面主要元素

2. **提示词组装节点**（LLM）
   - 模型：GPT-4
   - 提示词：
   ```
   为绘本页面生成完整提示词，严格按照10模块结构：
   
   【页码】：{{page_number}}
   【画面类型】：{{scene_type}}
   【整体风格】：{{style_prompt}}
   
   【人物角色】：
   {% for char in reference_images.characters %}
   {{char.name}}：（调用参考图，严格保持不变）
   位置与动作：[根据页面内容设计]
   {% endfor %}
   
   【非人物角色设计】：
   {% for item in reference_images.non_characters %}
   {{item.name}}：（调用参考图，严格保持不变）
   [位置和展示方式]
   {% endfor %}
   
   【场景设计】：
   {% if reference_images.scene %}
   （调用场景参考图，严格保持不变）
   {% endif %}
   
   【角色关系与构图】：
   [人物互动、视线关系]
   
   【时间与光线】：
   [时段、天气、光线]
   
   【镜头与景别】：
   [中景/远景、平视/俯视、构图]
   
   【常见错误清单提醒】：
   - 禁止高亮明艳色彩
   - 严禁数码光照
   - 人与物比例真实
   - 严禁改变人物样貌
   - 严禁改变场景结构
   
   页面内容：{{page_content}}
   ```

3. **格式验证节点**（Code）
   - 验证提示词完整性
   - 确保不超过800字

### 输出格式
```json
{
  "prompt": "【页码】：P1\n【画面类型】：真实场景\n...[完整提示词]",
  "modules": {
    "page_number": "P1",
    "scene_type": "真实场景",
    "style": "...",
    "characters": [...],
    "composition": "...",
    "lighting": "...",
    "shot": "..."
  }
}
```

---

## 工作流3：图片评选器（Gemini）

### 功能
自动评分并选择最佳生成图片。

### 输入变量
```json
{
  "images": [
    {"id": 1, "url": "https://..."},
    {"id": 2, "url": "https://..."}
  ],
  "page_content": "页面文本",
  "prompt": "生成时使用的提示词"
}
```

### 处理流程
1. **图片分析节点**（Vision LLM - Gemini Pro Vision）
   - 模型：Gemini 1.5 Pro
   - 提示词：
   ```
   你是专业绘本插画评审。请为以下图片评分（0-100分）。
   
   评分标准：
   1. 风格一致性（30分）：是否符合提示词风格
   2. 画面构图（25分）：构图是否合理、美观
   3. 内容准确性（25分）：是否准确表达页面内容
   4. 儿童友好性（20分）：是否适合{{target_age}}儿童
   
   页面内容：{{page_content}}
   提示词：{{prompt}}
   
   请为每张图片：
   1. 打分（0-100）
   2. 说明理由（50字以内）
   3. 推荐最佳图片
   
   输出JSON格式：
   {
     "scores": [85, 90, 78],
     "reasons": ["原因1", "原因2", "原因3"],
     "selected_index": 1
   }
   ```

2. **结果处理节点**（Code）
   ```python
   def main(evaluation_result):
       result = json.loads(evaluation_result)
       # 确保selected_index是得分最高的
       max_score_index = result["scores"].index(max(result["scores"]))
       result["selected_index"] = max_score_index
       return result
   ```

### 输出格式
```json
{
  "selected_index": 1,
  "scores": [85, 90, 78],
  "reasons": [
    "构图较好但色彩略深",
    "最符合要求，推荐",
    "人物比例有轻微问题"
  ]
}
```

---

## 配置步骤

### 1. 创建工作流
1. 登录Dify
2. 进入"工作流"页面
3. 点击"创建工作流"
4. 选择"从空白开始"

### 2. 添加节点
根据上述流程图添加各个节点：
- LLM节点：用于AI处理
- Code节点：用于数据处理
- 条件节点：用于分支逻辑
- 输出节点：定义最终输出

### 3. 配置LLM节点
- 选择模型（推荐GPT-4或Claude Sonnet）
- 设置温度（0.7左右）
- 配置输出格式（JSON或Text）

### 4. 测试工作流
使用示例数据测试每个工作流，确保：
- 输入输出格式正确
- LLM响应符合预期
- 错误处理完善

### 5. 发布并获取API
1. 点击"发布"
2. 复制工作流ID
3. 将ID填入后端 `.env` 文件

---

## 常见问题

### Q1: 提示词生成不符合格式？
A: 在LLM节点中添加更严格的格式要求，使用Few-shot示例。

### Q2: Gemini无法分析图片？
A: 确保使用Gemini Pro Vision模型，图片URL可访问。

### Q3: 工作流运行超时？
A: 增加超时时间设置，或优化提示词减少token消耗。

### Q4: 如何调试工作流？
A: 使用Dify的测试功能，逐节点查看输出。

---

## 进阶优化

1. **提示词模板化**：将常用风格存为模板
2. **多语言支持**：添加语言选择参数
3. **历史记录**：保存成功案例用于Few-shot
4. **A/B测试**：创建工作流变体对比效果

---

## 相关资源

- [Dify官方文档](https://docs.dify.ai/)
- [工作流最佳实践](https://docs.dify.ai/guides/workflow)
- [LLM提示词工程](https://www.promptingguide.ai/)
