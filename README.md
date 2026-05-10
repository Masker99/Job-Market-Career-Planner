# Job Market Career Planner

基于岗位市场数据的 RAG 职业转型规划助手。项目会从本地岗位 Markdown 数据中检索与用户背景、目标方向最相关的岗位要求，再调用 LLM 生成定制化转型路径、技能差距、作品集计划和投递策略。

## 项目目标

这个项目用于学习并演示 RAG 的核心链路：

```text
岗位数据
  -> 文档切片
  -> LLM 查询扩展
  -> 关键词检索
  -> 候选岗位市场画像
  -> 代表性 Top-K 岗位证据
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

其中“简历文件”和“补充个人信息”至少需要填写一个。默认会先把完整本地输出保存到 `outputs/`，再把脱敏后的可提交版本保存到 `reports/`。

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

完整本地输出默认保存为类似：

```text
outputs/v4_20260510_001530_career_plan.md
```

脱敏后的 GitHub 版本默认保存为类似：

```text
reports/v4_20260510_001530_career_plan.md
```

### 5. 查看 RAG 检索调试报告

V2 增加了 `--debug` 参数，用来观察本次 RAG 运行到底检索了什么、为什么命中、哪些上下文被放进 Prompt。

```powershell
python main.py --profile "我有 3 年 RPA 开发经验，熟悉 Python 和自动化流程。" --target-role "AI Agent 开发工程师" --debug
```

默认会额外生成：

```text
outputs/v4_20260510_001530_retrieval_debug.md
reports/v4_20260510_001530_retrieval_debug.md
```

调试报告包含：

- Retrieval Query：本次用于检索岗位库的查询文本
- Query Expansion：LLM 生成的扩展岗位、相关技能、相关工具和最终检索词
- Market Profile：基于更多候选岗位统计出的市场画像
- Retrieved Jobs：命中的岗位、分数、关键词和原文预览
- Prompt Context Preview：最终塞给 LLM 的岗位上下文
- System Prompt / Final User Prompt Preview：最终提示词预览

也可以自定义调试报告输出位置：

```powershell
python main.py --profile "熟悉 Python、RAG 和 FastAPI" --target-role "AI 应用工程师" --debug --debug-output outputs/my_debug.md
```

如果要显式指定版本前缀，可以使用：

```powershell
python main.py --profile "熟悉 Python、RAG 和 FastAPI" --target-role "AI 应用工程师" --debug --report-version v4
```

建议把 `reports/` 中有代表性的运行结果提交到 GitHub，用来记录每个版本的输出质量、检索证据和调试过程。`reports/` 是脱敏副本，会遮盖用户背景、简历内容和最终用户 Prompt 预览。`outputs/` 保存完整本地结果，默认不会提交。

如果只想生成本地完整输出，不生成 `reports/` 脱敏副本，可以使用：

```powershell
python main.py --profile "熟悉 Python、RAG 和 FastAPI" --target-role "AI 应用工程师" --debug --no-report-copy
```

## 配置项

| 环境变量 | 说明 |
|---|---|
| `JMCP_JOB_DATA_DIR` | 岗位 Markdown 数据目录 |
| `JMCP_RESUME_DIR` | 简历/个人背景资料目录 |
| `JMCP_TOP_K` | 最终放进 Prompt 的代表性岗位片段数量 |
| `JMCP_MARKET_TOP_K` | 用于生成市场画像的候选岗位数量 |
| `JMCP_QUERY_EXPANSION_MODE` | 查询扩展模式，`off` 保持 V3，`llm` 使用 LLM 扩展 |
| `JMCP_QUERY_EXPANSION_MAX_TERMS` | 最多参与检索的扩展词数量 |
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
│   ├── query_expander.py # LLM 查询扩展
│   ├── retriever.py     # 关键词检索
│   ├── market_profile.py # 市场画像统计
│   ├── debug.py         # RAG 调试报告
│   ├── llm.py           # LLM / mock 调用
│   ├── planner.py       # RAG 规划链路
│   └── prompts.py       # Prompt 模板
├── data/
│   ├── jobs/            # 本地岗位数据，默认不提交
│   └── resume/          # 本地简历资料，默认不提交
├── outputs/             # 本地临时运行输出，默认不提交
├── reports/             # 可提交的版本化运行报告
├── main.py              # CLI 入口
├── .env.example
└── requirements.txt
```

## 当前版本

V4：LLM Query Expansion RAG

在 V3 Market Profile RAG 的基础上，V4 在检索前增加 LLM Query Expansion。系统会先让 LLM 把用户输入的目标岗位改写成更贴近岗位市场的表达，再进入关键词检索和市场画像统计。这个版本重点学习 RAG 里的 Query Transformation / Query Rewriting。

- 从岗位 Markdown 文件加载职位信息
- 按 `## 职位` 切分岗位片段
- 提取岗位标题、技能点和完整描述
- 根据目标方向、重点技能和用户背景生成原始检索 query
- 使用 LLM 扩展近义岗位、相关技能、相关工具和最终检索词
- 对标题、技能点、正文设置不同检索权重
- 先召回 `JMCP_MARKET_TOP_K` 个候选岗位，用于生成市场画像
- 统计高频技能、高频岗位标题、命中关键词、经验、学历和薪资分布
- 再取 `JMCP_TOP_K` 个代表性岗位作为证据上下文
- 读取命令行背景或本地简历文件
- 检测到 PDF 简历时，自动转换为 Markdown 后继续处理
- 生成定制化转型计划
- 使用 `--debug` 生成带版本号和时间戳的调试报告
- 在调试报告中查看查询扩展、检索 query、市场画像、代表性岗位、匹配关键词、分数、上下文和 Prompt 预览

### V4 学习重点：Query Transformation

V1/V2 的重点是 Retrieval：如何把相关岗位找出来。V3 的重点是 Context Engineering：如何把找出来的一批岗位压缩成更有用的上下文。V4 的重点是 Query Transformation：用户输入不一定适合直接检索，系统可以先把用户目标改写成更贴近知识库和岗位市场的检索语言。

V4 的链路是：

```text
岗位数据
  -> LLM 扩展目标岗位表达
  -> 关键词召回更多候选岗位
  -> 统计市场画像
  -> 选择代表性岗位证据
  -> 市场画像 + 岗位证据 + 用户背景
  -> LLM 生成转岗计划
```

这样生成的规划不只服务于几个高分岗位，而是更接近“面向整个市场制定学习路线”。同时，V4 会缓解“用户说法”和“岗位数据说法”不一致的问题，例如把 `AI Agent 应用开发` 扩展为 `AI 应用工程师`、`LLM 应用开发`、`大模型应用开发`、`智能体开发`、`RAG 应用开发` 等更容易命中岗位市场的表达。

### V2 观察：关键词检索的局限

通过查看 `outputs/retrieval_debug.md` 可以发现，当前 Retrieval 主要依赖关键词的一一匹配和位置权重。它能清楚解释“为什么某个岗位被召回”，但也会比较生硬。

例如用户目标是：

```text
AI Agent 应用开发
```

当前关键词检索更容易给标题或技能里直接出现 `AI Agent`、`Agent`、`应用开发` 的岗位加高分。但对人来说明显相关的表达，例如：

```text
AI 应用工程师
LLM 应用开发
大模型应用开发
智能体开发
AI 自动化工程师
```

如果字面关键词重合不够，当前版本可能不会给出足够高的分数。

这个观察说明，RAG 里的 Retrieval 不只是“找到完全相同的词”，更重要的是把用户的表达映射到岗位数据里的相近表达。后续升级需要考虑：

- Query Expansion：给 `AI Agent 应用开发` 扩展同义词和近义词
- Embedding 语义检索：匹配“词不一样但意思相近”的岗位
- Hybrid Search：同时保留关键词检索的精确命中和向量检索的语义召回

### V2 观察：Top-K 岗位不等于市场画像

继续查看调试报告还可以发现，当前系统最终只把匹配分数最高的少数 Top-K 岗位交给 LLM。这个方式适合回答“哪些岗位最像当前目标”，但职业转岗计划不应该只服务于几个特定岗位。

更理想的转岗规划应该面向整个岗位市场：

- 从更多岗位中统计反复出现的技能要求
- 区分高频必备技能、常见加分项和少数岗位才要求的技能
- 观察岗位职责、薪资、经验、学历等维度的整体分布
- 基于市场共性制定学习路线，而不是只跟随某几个高分岗位

这样生成的学习计划会更稳：既能覆盖主流岗位要求，也能避免被个别岗位的特殊要求带偏。对后续面试来说，也更容易形成底气和选择空间，因为学习目标来自“市场共性”，而不是某一两个岗位样本。

这个观察说明，项目后续需要从单纯的 Top-K RAG，升级为“检索 + 市场统计 + 证据生成”的组合流程：

```text
岗位数据
  -> 大范围召回候选岗位
  -> 技能/职责/薪资/经验统计
  -> 提炼市场画像
  -> 再选择代表性岗位证据
  -> 生成转岗计划
```

也就是说，后续的 Retrieval 不只要找“最相似的几个岗位”，还要支持 Market Profile：让规划建立在更完整的市场分布上。

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
