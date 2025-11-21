# MailBridge: IMAP to WebDAV Sync

一款专为 Vercel 平台设计的自动化工具。它能作为一座桥梁，监控指定的 IMAP 邮箱，并将符合特定主题邮件的附件自动同步到 WebDAV 服务器。

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fomskk%2FEmailFileBackup-Cron.git&env=DATABASE_URL,IMAP_HOSTNAME,IMAP_USERNAME,IMAP_PASSWORD,WEBDAV_SERVERS,EMAIL_SEARCH_SUBJECT,API_SECRET_KEY,INTERNAL_API_KEY,WEB_AUTH_USER,WEB_AUTH_PASSWORD&project-name=mailbridge-imap-to-webdav&repository-name=mailbridge-imap-to-webdav)

## ✨ 主要功能

### 核心功能
- **一键部署**: 通过 Vercel 按钮，只需几步即可完成部署
- **无服务器架构**: 完美运行在 Vercel 上，无需管理自己的服务器
- **邮件监控**: 通过 IMAP 连接邮箱，实时监控新邮件
- **关键字过滤**: 只处理邮件主题包含特定关键字的邮件
- **附件同步**: 自动提取附件并上传到 WebDAV 服务器

### 高级特性
- **多服务器支持**: 支持配置和管理多个 WebDAV 服务器
- **服务器管理**: 可视化界面手动选择默认上传服务器
- **WebDAV 文件浏览**: 简洁的在线文件浏览和下载
- **智能限制**: 支持附件大小限制和批量处理限制，避免资源耗尽
- **日志记录**: 所有同步活动记录在 MySQL 数据库中，显示上传到的服务器
- **现代化 Web 界面**: 🎨 极简设计风格,提供受密码保护的管理界面
  - 📊 Dashboard 统计面板（总日志数、成功率、活跃服务器）
  - 📋 日志查看与搜索（支持自动刷新）
  - 📁 WebDAV 文件浏览器（中文界面）
  - 🖥️ 服务器管理（可视化配置 + 连接测试）
  - 🔔 Toast 通知系统（右上角浮动通知）
  - 📱 响应式设计（完美支持桌面和移动设备）

### 安全与性能
- **Session 登录**: 基于 Flask-Session 的现代化登录系统
- **并发安全**: 通过数据库分布式锁，确保高频调用下的稳定性
- **性能优化**: 数据库连接池、配置缓存、索引优化
- **健康检查**: 提供 `/health` 端点用于服务监控

## 🚀 一键部署指南

1.  **点击上方 "Deploy with Vercel" 按钮**
2.  **授权 Vercel**: 登录并授权 Vercel 访问您的 GitHub 账户
3.  **配置环境变量**: 填写所有必需的环境变量（见下表）
4.  **部署**: 点击 "Deploy"，等待部署完成

### 必需环境变量

| 变量名                | 说明                                      | 示例                          |
|-----------------------|-------------------------------------------|-------------------------------|
| `DATABASE_URL`        | MySQL 数据库连接字符串                     | `mysql://user:pass@host/db`  |
| `IMAP_HOSTNAME`       | IMAP 服务器地址                           | `imap.example.com`           |
| `IMAP_USERNAME`       | IMAP 登录用户名                           | `user@example.com`           |
| `IMAP_PASSWORD`       | IMAP 登录密码                             | `your_password`              |
| `WEBDAV_SERVERS`      | WebDAV 服务器配置（JSON 数组）             | 见下方示例                    |
| `EMAIL_SEARCH_SUBJECT`| 邮件搜索主题关键词                         | `keyword`                    |
| `API_SECRET_KEY`      | API 端点保护密钥                          | `random_key_123`             |
| `INTERNAL_API_KEY`    | 内部 Worker 保护密钥                      | `another_key_456`            |
| `WEB_AUTH_USER`       | Web 界面登录用户名                        | `admin`                      |
| `WEB_AUTH_PASSWORD`   | Web 界面登录密码                          | `secure_password`            |
| `FLASK_SECRET_KEY`    | Session 加密密钥（建议32+字符，可选）          | - |

### 可选配置

| 变量名                   | 描述                                | 默认值 |
| ------------------------ | ----------------------------------- | ------ |
| `LOG_LEVEL`              | 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL） | INFO   |
| `LOG_FORMAT`             | 日志格式（console/detailed/simple） | console|
| `MAX_ATTACHMENT_SIZE_MB` | 单个附件最大大小限制 (MB)           | 50     |
| `MAX_EMAILS_PER_RUN`     | 每次运行最多处理的邮件数量          | 10     |

#### 日志配置说明

- **LOG_LEVEL**: 控制日志输出的详细程度
  - `DEBUG`: 显示所有调试信息（开发环境推荐）
  - `INFO`: 显示常规操作信息（生产环境推荐）
  - `WARNING`: 只显示警告和错误
  - `ERROR`: 只显示错误信息
  - `CRITICAL`: 只显示严重错误

- **LOG_FORMAT**: 控制日志显示格式
  - `console`: 易读格式，带时间戳和emoji（推荐）
  - `detailed`: 详细格式，包含文件名和行号
  - `simple`: 简洁格式，只显示级别和消息


### WebDAV 服务器配置

> **⚠️ 重要提示**：首次启动后，环境变量中的服务器配置会自动导入到数据库中。之后应该通过 `/servers` Web 界面管理服务器，而不是修改环境变量。

使用 `WEBDAV_SERVERS` 环境变量配置一个或多个 WebDAV 服务器（JSON 数组格式）：

**单服务器示例**：
```bash
WEBDAV_SERVERS='[{"name":"Main","url":"https://dav.example.com/dav","login":"username","password":"password"}]'
```

**多服务器示例**：
```bash
WEBDAV_SERVERS='[{"name":"Main","url":"https://dav.example.com/dav","login":"user","password":"pass"},{"name":"Backup","url":"https://backup.example.com/dav","login":"user","password":"pass"}]'
```

**JSON 格式**：
```json
[
  {
    "name": "Main",
    "url": "https://dav.example.com/dav",
    "login": "user",
    "password": "pass",
    "timeout": 60,
    "chunk_size": 8192
  },
  {
    "name": "Backup",
    "url": "https://backup.example.com/dav",
    "login": "user",
    "password": "pass"
  }
]
```

**字段说明**：
- `name`: 服务器名称（唯一标识）
- `url`: WebDAV 服务器 URL
- `login`: 登录用户名
- `password`: 登录密码
- `timeout`: 超时时间（秒，可选，默认60）
- `chunk_size`: 分块大小（字节，可选，默认8192）

## 📱 Web 界面

部署成功后，访问 Web 界面需要先登录。

### 🔒 登录系统

应用使用基于 **Session** 的现代化登录系统：

- **`/login`** - 登录页面
  - 简洁的登录表单
  - 输入 `WEB_AUTH_USER` 和 `WEB_AUTH_PASSWORD`
  - 错误密码会显示提示
  - 登录成功后跳转到首页

- **`/logout`** - 退出登录
  - 所有页面都有"退出"按钮
  - 退出后返回登录页

**安全特性**:
- ✅ Session 签名防止篡改
- ✅ 未登录访问自动跳转登录页
- ✅ 所有页面显示当前用户和退出按钮

### 🎨 现代化 UI 设计

应用采用**极简主义设计风格**，提供直观优雅的用户体验：

#### 设计特点
- 🎯 **固定侧边栏导航**: 清晰的页面结构，快速导航
- 🎨 **极简配色**: 中性色调 + 深紫色点缀，专业而不失活力
- 📱 **全响应式**: 移动端自适应，侧边栏可折叠
- 🔔 **Toast 通知**: 右上角优雅的浮动通知（替代传统弹窗）
- 🖼️ **SVG 图标**: 所有图标使用 Heroicons 风格的 SVG
- ✨ **流畅动画**: 微妙的过渡效果提升用户体验

#### 页面功能

- **`/`** - **概览面板**
  - 📊 Dashboard 统计卡片：总日志数、成功率、活跃服务器数
  - 🎯 快速操作入口：日志、文件浏览器、服务器管理
  
- **`/logs`** - **日志查看**
  - 📋 实时日志显示，支持分页
  - 🔍 文件名搜索功能
  - 🔄 可配置的自动刷新（10/30/60秒）
  - 📈 显示文件大小、上传状态、目标服务器

- **`/files`** - **文件浏览器**
  - 📁 多服务器切换浏览
  - 🔍 实时文件名搜索
  - 💾 在线下载文件
  - 🗂️ 面包屑导航
  - 🇨🇳 完整中文界面（文件名、大小、修改时间）

- **`/servers`** - **服务器管理**
  - ➕ 添加新的 WebDAV 服务器
  - ✏️ 编辑现有服务器配置
  - 🗑️ 删除不需要的服务器
  - 🔌 测试服务器连接（Toast 通知结果）
  - ⭐ 选择默认上传服务器
  - 🔄 启用/禁用服务器

### 📸 界面截图

#### 登录页面
![登录页面 - 简洁的登录表单,支持用户名密码认证](static/screenshots/login.png)

#### Dashboard 概览面板
![概览面板 - Dashboard 统计卡片显示总日志数、成功率和活跃服务器数](static/screenshots/dashboard.png)

#### 日志查看
![日志查看 - 实时显示上传历史,支持搜索和自动刷新](static/screenshots/logs.png)

#### 服务器管理
![服务器管理 - 可视化配置和管理多个 WebDAV 服务器](static/screenshots/servers.png)

#### 文件浏览器
![文件浏览器 - 多服务器文件浏览,完整中文界面](static/screenshots/files.png)



## 📊 API 端点

### 公开端点
- **`POST /api/run-task`** - 触发邮件处理任务
  - 认证: Bearer Token (`API_SECRET_KEY`)
  - 返回: 异步触发状态

- **`GET /health`** - 健康检查
  - 返回: 数据库和 WebDAV 连接状态

### 内部端点
- **`POST /api/internal/worker`** - 内部 worker 端点
  - 认证: Bearer Token (`INTERNAL_API_KEY`)
  - 由 `/api/run-task` 异步调用

### Web 端点
- **`GET /login`** - 登录页面
- **`POST /login`** - 处理登录
- **`GET /logout`** - 登出
- **`GET /`** - 概览面板（需要登录）
- **`GET /logs`** - 日志查看（需要登录）
- **`GET /files`** - 文件浏览器（需要登录）
- **`GET /files/download/<path>`** - 文件下载（需要登录）
- **`GET /servers`** - 服务器管理（需要登录）
- **`POST /servers/set-default`** - 设置默认服务器（需要登录）
- **`POST /servers/add`** - 添加服务器（需要登录）
- **`POST /servers/edit/<id>`** - 编辑服务器（需要登录）
- **`POST /servers/delete/<id>`** - 删除服务器（需要登录）
- **`POST /servers/test/<id>`** - 测试服务器连接（需要登录）

## 🕹️ 设置定时任务

部署成功后，设置定时任务定期调用 API 实现自动同步。

### 方式一：Vercel Cron Jobs（推荐）

在项目根目录的 `vercel.json` 文件中添加：

```json
{
  "crons": [
    {
      "path": "/api/run-task",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

> **注意**: Vercel Cron 会自动添加正确的认证头，无需手动配置。

### 方式二：第三方 Cron 服务

使用 Uptime Kuma、Cron-job.org 或 GitHub Actions 等服务：

```bash
curl -X POST https://your-project.vercel.app/api/run-task \
  -H "Authorization: Bearer YOUR_API_SECRET_KEY"
```

## 💻 本地开发

### 快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/omskk/EmailFileBackup-Cron.git
cd EmailFileBackup-Cron

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件填写配置

# 方式 2: 直接运行
python app.py
```

访问 `http://localhost:5002` 查看应用。

### macOS 端口说明

> ⚠️ **macOS 用户注意**: 系统的 AirPlay Receiver 服务默认占用 5000 和 5001 端口。为避免冲突，本项目默认使用 **5002** 端口。

**推荐做法**:
- 或在 `.env` 中设置 `FLASK_RUN_PORT=5002`

## 🗂️ 项目结构

```
mail_to_webdav/
├── app.py                 # Flask 应用主文件
├── config.py              # 配置管理
├── database.py            # 数据库操作
├── mail_processor.py      # 邮件处理逻辑
├── logger.py              # 统一日志配置
├── requirements.txt       # Python 依赖
├── static/                # 静态资源
│   ├── css/
│   │   └── style.css     # 全局样式（极简设计系统）
│   └── favicon.png       # 网站图标
├── templates/             # HTML 模板
│   ├── base.html         # 基础模板（侧边栏导航）
│   ├── index.html        # 概览面板
│   ├── login.html        # 登录页面  
│   ├── logs.html         # 日志页面
│   ├── servers.html      # 服务器管理
│   └── webdav.html       # 文件浏览器
└── .env.example          # 环境变量示例
```

## 🛠️ 技术栈

- **框架**: Python 3.x, Flask
- **部署**: Vercel (无服务器)
- **数据库**: MySQL (with connection pooling)
- **认证**: Flask-Session (基于 Session 的登录)
- **邮件**: imbox (IMAP)
- **WebDAV**: webdavclient3
- **前端**: 原生 HTML/CSS/JavaScript (极简设计，无框架依赖)
- **图标**: SVG (Heroicons 风格)
- **其他**: python-dotenv, requests, mysql-connector-python

## 📖 使用流程

1. **首次启动**: 应用会自动创建数据库表并导入环境变量中的服务器配置
2. **登录界面**: 访问应用，使用配置的用户名密码登录
3. **查看统计**: 在概览面板查看总日志数、成功率等统计信息
4. **配置服务器**: 访问 `/servers` 页面管理 WebDAV 服务器，选择默认上传目标
5. **自动同步**: 定时任务触发，处理符合条件的邮件并上传附件
6. **查看日志**: 在 `/logs` 页面查看上传历史和状态
7. **浏览文件**: 在 `/files` 页面浏览和下载已上传的文件

## 🔒 安全建议

- ✅ 使用强密码（32+ 字符）作为 API 密钥
- ✅ 为 `FLASK_SECRET_KEY` 生成随机密钥（用于 Session 加密）
- ✅ 为邮箱启用应用专用密码（而非主密码）
- ✅ 定期检查上传日志，确保无异常活动
- ✅ 在生产环境使用 HTTPS
- ✅ 限制数据库访问权限
- ✅ 设置合理的附件大小限制

## 📝 常见问题

**Q: 如何配置多个 WebDAV 服务器？**  
A: 在环境变量中设置 `WEBDAV_SERVERS`（JSON 数组），首次启动后通过 `/servers` Web 界面管理。

**Q: 如何切换默认上传服务器？**  
A: 访问 `/servers` 页面，点击要设为默认的服务器左侧的单选按钮。

**Q: 邮件处理失败怎么办？**  
A: 检查 `/logs` 页面的错误信息，或查看 Vercel 日志排查问题。

**Q: 支持哪些 WebDAV 服务？**  
A: 支持所有标准 WebDAV 服务，包括 Nextcloud、ownCloud、InfiniCLOUD、坚果云等。


**Q: 如何测试服务器连接？**  
A: 在 `/servers` 页面点击服务器的"测试"按钮，右上角会显示 Toast 通知结果。

**Q: UI 在移动设备上如何显示？**  
A: 应用采用响应式设计，移动端会自动调整布局，侧边栏可通过汉堡菜单切换。

## 🎨 UI 预览

应用采用现代极简设计风格：
- 固定侧边栏导航，快速切换页面
- Dashboard 统计卡片，一目了然
- Toast 通知系统，优雅提示
- 全中文界面，无障碍使用
- SVG 图标，清晰美观
- 响应式布局，移动友好

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Happy Syncing! 📧 ➡️ ☁️**
