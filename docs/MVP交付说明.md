# 招聘知识协同 SaaS MVP

日期：2026-11-19。场景沿用此前的“招聘需求澄清与面试协同”（fsg-recruiting），代码仓库仍为 `wujunzhu0802/fde-recruiting-collaboration`。11月5日的无AI流程图继续表示现状，不被新MVP替换。

## 五项要求对应实现

1. **FastAPI**：`mvp/app.py`，注册登录、知识页增改、知识图谱、问答、运行追踪、租户订阅、用户管理与审计接口；Pydantic输入约束，SQLite持久化。`/docs`是OpenAPI交互文档，`/openapi.json`是接口契约。
2. **Harness**：`mvp/rag.py`和`mvp/evaluate.py`。运行步骤是授权→只读检索→生成或明确摘录→引用校验；每次至多1次模型调用、4个证据块、20秒模型超时、900输出token。不提供生产写入工具。失败进入原文摘录，依据不足明确拒答，保留逐步轨迹及审计。这里Harness指Agent运行与评估框架，不是Harness商业CI/CD产品。
3. **知识库**：Wiki纯文本/Markdown原文编辑，乐观版本锁；500字符分块、80字符重叠，以本地TF-IDF中文双字词向量余弦进行RAG；文档标签和Wiki引用形成图谱；OpenAI兼容HTTPS LLM适配器。当前不是云端语义Embedding或Neo4j推理引擎。未配置API Key时清楚显示`extractive`，不冒充LLM生成；真正调用模型需配置环境变量。
4. **权限**：密码scrypt加盐，8小时不透明令牌（仅存SHA256），HttpOnly/SameSite Cookie或Bearer；后端每次读取当前用户权限。SaaS管理员管理租户与订阅；组织管理员管理本租户Wiki与用户；成员可问答；访客只读Wiki。基础用户每日20次问答、只读基础页；专业用户每日200次并可读取专业知识。租户与层级在检索前过滤，图谱也按同一权限过滤。SaaS管理员没有默认读取各组织知识正文的接口。
5. **网址部署**：已运行真实FastAPI进程，并通过独立Cloudflare Quick Tunnel暴露HTTPS；当前地址及公网实际检查见`mvp-deployment.json`。这是依赖本机进程的临时演示，不是7×24云托管。根目录Dockerfile和render.yaml提供长期部署配置，但尚未使用外部云账户部署。

## 如何访问

打开部署记录中的HTTPS地址，选择“创建组织与账号”，自行设置至少10位密码。注册默认创建独立基础组织和组织管理员。知识页是合成样本，无须提交真实简历或个人资料。

SaaS管理员账号首启时生成；其凭据**仅存本机** `runtime/mvp/admin-credentials.txt`，不写入仓库、部署记录或网页。登录后可调整租户订阅，再由组织管理员创建专业成员。当前没有订阅收费、忘记密码、邮件验证和企业SSO功能，不能视为完整商业SaaS。

## 本地运行与模型配置

```powershell
python -m pip install -r mvp/requirements.txt
python -m uvicorn mvp.app:app --host 127.0.0.1 --port 8088
```

首次启动前可设置 `MVP_ADMIN_EMAIL` 和 `MVP_ADMIN_PASSWORD`；已有管理员时环境变量不会重置其密码。HTTPS部署设置 `MVP_SECURE_COOKIES=1`。本地HTTP调试保持0。数据库默认 `runtime/mvp/data.sqlite`，可用 `MVP_DB` 指向持久卷。

LLM选项：`MVP_LLM_API_KEY`、`MVP_LLM_BASE_URL`（仅HTTPS、OpenAI兼容Chat Completions）、`MVP_LLM_MODEL`。不要把密钥放前端或提交Git。服务不会自动读取`.env`；示例是配置清单，应通过运行环境注入。当前实际演示没有API Key，运行的是本地RAG+摘录；模型适配器的成功、超时和非法引用路径使用测试替身验证，尚未执行真实模型评估。

## 评估与已知限制

```powershell
python -m mvp.evaluate
node --check mvp/web/app.js
```

实际结果见`mvp-evaluation.json`，覆盖19项ASGI集成测试。真实模型效果、浏览器视觉/交互走查、Docker镜像构建及Render云上线尚未验证。当前执行环境缺少可用的浏览器控制接口，因此只执行HTTP接口与前端语法检查，不宣称完成浏览器端验收。

知识来源为此前合成访谈与规则分析的人工整理，种子文档标注合成性质。当前Wiki只保存最新正文和版本号，历史问答保留当时证据片段；没有完整Wiki修订历史。备份、保留期限、监控值守、配额计费、防注册滥用及可观测性完善后才适合正式生产。

## 长期部署

`docker build -t recruiting-mvp .`，通过私有环境变量注入配置、挂载 `/app/runtime` 数据卷、映射8080端口，并配置可信反向代理及HTTPS。render.yaml需要Render账号，并使用带持久卷的收费服务；本次未购买或创建收费资源。部署后应验证跨租户隔离、模型来源、HTTPS Cookie、数据库备份与恢复，再替换临时演示地址。

参考：[FastAPI安全示例](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)、[Cloudflare Quick Tunnel说明](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)。Quick Tunnel官方明确仅供开发测试，停止进程后地址失效。
