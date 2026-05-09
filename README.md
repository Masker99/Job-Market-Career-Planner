# Job Market Career Planner

基于岗位市场数据的 RAG 职业转型规划助手。项目会从本地岗位 Markdown 数据中检索与用户背景、目标方向最相关的岗位要求，再调用 LLM 生成定制化转型路径、技能差距、作品集计划和投递策略。

## 项目目标

这个项目用于学习并演示 RAG 的核心链路：

```text
岗位数据
  -> 文档切片
  -> 关键词检索
  -> Top-K 岗位上下文
  -> Prompt 组装
  -> LLM 生成转型计划
```

第一版不使用向量数据库，先用关键词检索跑通 RAG MVP。后续可以升级为 Embedding + Chroma/FAISS。

## 数据目录

```text
data/jobs/    # 放采集到的岗位数据，例如 岗位信息采集数据表_*.md
data/resume/  # 放个人简历或背景资料，支持 .pdf / .txt / .md
```

真实岗位数据和个人简历默认不会提交到 GitHub，目录里只保留 `.gitkeep` 用来占位。

## 快速开始

### 1. 创建虚拟环境

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`：

```powershell
Copy-Item .env.example .env
```

学习和调试时可以先使用 mock：

```env
JMCP_MOCK=1
```

将岗位 Markdown 数据放到：

```text
data/jobs/
```

将个人简历或背景资料放到：

```text
data/resume/
```

如果放入的是 PDF 简历，程序会先自动提取文本，并在同目录生成一个同名 Markdown 文件，例如：

```text
data/resume/my_resume.pdf -> data/resume/my_resume.md
```

### 4. 运行

交互式运行：

```powershell
python main.py
```

程序会依次询问：

```text
目标岗位/方向
简历文件名或路径，可跳过
补充个人信息，可跳过
```

其中“简历文件”和“补充个人信息”至少需要填写一个。输出文件默认保存到 `outputs/career_plan.md`。

方式一：直接传入个人背景。

```powershell
python main.py --profile "我有 3 年 RPA 开发经验，熟悉 Python、UiPath、Flask 和业务流程自动化。" --target-role "AI 应用工程师 / AI Agent 应用开发"
```

方式二：读取 `data/resume/` 下的简历文件。

```powershell
python main.py --resume-file my_resume.md --target-role "AI 应用工程师 / AI Agent 应用开发"
```

PDF 简历也可以直接传入：

```powershell
python main.py --resume-file my_resume.pdf --target-role "AI 应用工程师 / AI Agent 应用开发"
```

也可以同时传入 `--profile` 和 `--resume-file`，系统会合并两部分信息。

输出文件默认保存到：

```text
outputs/career_plan.md
```

### 5. 查看 RAG 检索调试报告

V2 增加了 `--debug` 参数，用来观察本次 RAG 运行到底检索了什么、为什么命中、哪些上下文被放进 Prompt。

```powershell
python main.py --profile "我有 3 年 RPA 开发经验，熟悉 Python 和自动化流程。" --target-role "AI Agent 开发工程师" --debug
```

默认会额外生成：

```text
outputs/retrieval_debug.md
```

调试报告包含：

- Retrieval Query：本次用于检索岗位库的查询文本
- Retrieved Jobs：命中的岗位、分数、关键词和原文预览
- Prompt Context Preview：最终塞给 LLM 的岗位上下文
- System Prompt / Final User Prompt Preview：最终提示词预览

也可以自定义调试报告输出位置：

```powershell
python main.py --profile "熟悉 Python、RAG 和 FastAPI" --target-role "AI 应用工程师" --debug --debug-output outputs/my_debug.md
```

## 配置项

| 环境变量 | 说明 |
|---|---|
| `JMCP_JOB_DATA_DIR` | 岗位 Markdown 数据目录 |
| `JMCP_RESUME_DIR` | 简历/个人背景资料目录 |
| `JMCP_TOP_K` | 检索返回的岗位片段数量 |
| `JMCP_MOCK` | 是否启用 mock 模式 |
| `JMCP_DOMAIN` | 职业规划领域 |
| `JMCP_ADVISOR_ROLE` | LLM 扮演的顾问角色 |
| `JMCP_DEFAULT_TARGET_ROLE` | 未传 `--target-role` 时使用的默认目标方向 |
| `JMCP_FOCUS_KEYWORDS` | 检索与规划重点关注的技能关键词 |
| `JMCP_AVOID_DIRECTIONS` | 默认不优先推荐的方向 |
| `JMCP_OUTPUT_LANGUAGE` | 输出语言 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_MODEL` | 模型名称 |
| `DEEPSEEK_TEMPERATURE` | 生成温度 |

## 项目结构

```text
.
├── app/
│   ├── config.py        # 环境变量配置
│   ├── loader.py        # 加载并切分岗位 Markdown
│   ├── resume_loader.py # 读取简历/个人背景文件
│   ├── retriever.py     # 关键词检索
│   ├── llm.py           # LLM / mock 调用
│   ├── planner.py       # RAG 规划链路
│   └── prompts.py       # Prompt 模板
├── data/
│   ├── jobs/            # 本地岗位数据，默认不提交
│   └── resume/          # 本地简历资料，默认不提交
├── outputs/             # 运行输出，默认不提交
├── main.py              # CLI 入口
├── .env.example
└── requirements.txt
```

## 当前版本

V2：可观测关键词 RAG

在 V1 关键词 RAG 的基础上，V2 增加了检索调试报告，让 RAG 链路从黑盒变成可观察流程。

- 从岗位 Markdown 文件加载职位信息
- 按 `## 职位` 切分岗位片段
- 提取岗位标题、技能点和完整描述
- 根据目标方向、重点技能和用户背景生成检索 query
- 对标题、技能点、正文设置不同检索权重
- 取 Top-K 相关岗位作为上下文
- 读取命令行背景或本地简历文件
- 检测到 PDF 简历时，自动转换为 Markdown 后继续处理
- 生成定制化转型计划
- 使用 `--debug` 生成 `outputs/retrieval_debug.md`
- 在调试报告中查看检索 query、命中岗位、匹配关键词、分数、上下文和 Prompt 预览

## 设计说明

项目不会直接用用户旧简历全文作为唯一检索条件。很多转行用户的旧背景里可能没有目标岗位关键词，所以当前设计会拆成：

```text
用户背景：用于分析已有能力和差距
目标方向：用于检索岗位市场要求
```

如果不传 `--target-role`，系统会使用 `.env` 中的 `JMCP_DEFAULT_TARGET_ROLE`。

岗位检索也不会只看标题。岗位标题重复度很高，真正关键的技能通常出现在技能点和岗位描述里。因此项目会提取：

```text
title   -> 判断岗位方向
skills  -> 判断技术要求
content -> 补充上下文
```

并对技能命中给更高权重。

## 后续升级

- 增加 Embedding + 向量数据库，升级为语义检索
- 增加 Hybrid Search，组合关键词检索和向量检索
- 增加 Rerank，对召回岗位进行二次排序
- 增加 RAG Evaluation，用固定样例评估检索质量
- 增加岗位技能词频统计
- 增加薪资、经验、学历维度分析
- 增加 FastAPI 服务接口
- 增加前端页面
