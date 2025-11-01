# Flask NAS 文件浏览器

一个轻量级的 Web 文件管理系统，用于在阿里云函数计算（FC）中直接管理 NAS 文件系统。提供直观的图形界面来浏览、上传、下载、创建和删除文件及文件夹。

## ⚠️ 重要安全警告

**此应用不包含任何用户认证机制！**

任何能够访问此应用的人都将拥有对指定目录下所有文件的完全控制权（读、写、删除）。

**绝对不能部署在公共互联网上！**

此应用仅适用于：
- 安全的家庭局域网
- 公司内网
- 通过 VPN 访问的私有网络
- 其他受信任的隔离环境

## 功能特性

- 📁 **目录浏览**：清晰的文件和文件夹列表，支持层级导航
- ⬆️ **文件上传**：支持同时上传多个文件
- ⬇️ **文件下载**：一键下载任意文件
- ➕ **创建文件夹**：快速创建新文件夹组织文件
- 🗑️ **删除操作**：删除文件或文件夹（包括非空文件夹）
- 🍞 **面包屑导航**：快速跳转到任意上级目录
- 🎨 **现代化界面**：基于 Bootstrap 5 的响应式设计
- 📱 **移动端适配**：在手机和平板上也能流畅使用
- 🔒 **路径安全**：防止目录遍历攻击，限制访问范围

## 文件类型图标

应用会根据文件扩展名显示不同的图标：

- 📷 图片文件（jpg, png, gif, svg 等）
- 🎬 视频文件（mp4, avi, mkv 等）
- 🎵 音频文件（mp3, wav, flac 等）
- 📄 文档文件（pdf, doc, xls, txt 等）
- 📦 压缩文件（zip, rar, 7z 等）
- 💻 代码文件（py, js, java, c 等）

## 系统要求

- Python 3.7+
- Linux/Unix 系统（推荐 Debian/Ubuntu）
- NAS 文件系统挂载（默认 `/mnt/nas`）

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd fc_flask_nas
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

或者使用虚拟环境（推荐）：

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. 运行应用

```bash
python3 app.py
```

应用将在 `http://0.0.0.0:5000` 上运行。

### 4. 访问应用

在浏览器中打开：
- 本地访问：`http://localhost:5000`
- 局域网访问：`http://<服务器IP>:5000`

## 配置说明

### 环境变量

应用支持以下环境变量配置：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `BASE_DIR` | 文件浏览的根目录 | `/mnt/nas` |
| `SECRET_KEY` | Flask 密钥（用于会话加密） | `dev-secret-key-change-in-production` |

#### 示例：自定义根目录

```bash
# Linux/Mac
export BASE_DIR="/path/to/your/directory"
python3 app.py

# Windows
set BASE_DIR="C:\path\to\your\directory"
python3 app.py
```

### 生产环境部署

#### 使用 Gunicorn（推荐）

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

参数说明：
- `-w 4`：使用 4 个工作进程
- `-b 0.0.0.0:5000`：绑定到所有网络接口的 5000 端口

#### 使用 systemd 服务（Debian/Ubuntu）

创建服务文件 `/etc/systemd/system/flask-nas.service`：

```ini
[Unit]
Description=Flask NAS File Browser
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/fc_flask_nas
Environment="BASE_DIR=/mnt/nas"
Environment="SECRET_KEY=your-secret-key-here"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start flask-nas
sudo systemctl enable flask-nas  # 开机自启
```

#### 使用 Nginx 反向代理

编辑 Nginx 配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间（用于大文件上传）
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
        
        # 增加最大上传大小
        client_max_body_size 10G;
    }
}
```

## 阿里云函数计算部署

### 准备工作

1. 确保已创建 NAS 文件系统并挂载到函数计算
2. NAS 挂载路径为 `/mnt/nas`（或通过环境变量指定）

### 部署步骤

1. 将项目文件打包上传到函数计算
2. 配置函数：
   - 运行时：Python 3.9+
   - 启动命令：`gunicorn -w 1 -b 0.0.0.0:9000 app:app`
   - 端口：9000
3. 设置环境变量：
   - `BASE_DIR=/mnt/nas`
4. 配置 NAS 挂载点
5. 触发器：HTTP 触发器

## 使用说明

### 浏览文件

- 点击文件夹名称进入子目录
- 点击面包屑导航快速返回上级目录
- 文件夹始终显示在文件前面

### 上传文件

1. 点击"选择文件"按钮
2. 选择一个或多个文件（支持多选）
3. 点击"上传文件"按钮
4. 如果文件名重复，系统会自动添加数字后缀

### 下载文件

- 点击文件名即可下载

### 创建文件夹

1. 在"创建文件夹"输入框中输入文件夹名称
2. 点击"创建文件夹"按钮
3. 新文件夹将在当前目录下创建

### 删除文件/文件夹

1. 点击文件或文件夹右侧的"删除"按钮
2. 确认删除操作
3. **注意**：删除文件夹会递归删除其所有内容，无法恢复！

## 技术栈

- **后端框架**：Flask 3.0
- **前端框架**：Bootstrap 5
- **图标库**：Bootstrap Icons
- **模板引擎**：Jinja2
- **WSGI 服务器**：Gunicorn

## 项目结构

```
fc_flask_nas/
├── app.py                  # Flask 主应用
├── templates/              # 模板目录
│   ├── index.html         # 主页面模板
│   └── 404.html           # 404 错误页面
├── requirements.txt        # Python 依赖
├── .gitignore             # Git 忽略配置
└── README.md              # 项目文档
```

## 安全机制

### 路径验证

应用实现了严格的路径验证机制：
- 使用 `os.path.realpath()` 解析真实路径
- 验证所有路径都在 `BASE_DIR` 范围内
- 防止 `../` 等目录遍历攻击
- 拒绝访问符号链接指向的外部文件

### 文件名处理

- 使用 `werkzeug.utils.secure_filename()` 处理上传文件名
- 移除文件名中的危险字符
- 防止路径注入攻击

### 操作确认

- 删除操作需要用户二次确认
- 使用 POST 方法执行修改操作（而非 GET）

## 后续扩展计划

- [ ] 图片在线预览功能
- [ ] 视频在线播放功能
- [ ] 文档在线编辑功能
- [ ] 文件搜索功能
- [ ] 批量操作（批量下载、批量删除）
- [ ] 文件压缩/解压功能
- [ ] 用户认证系统（可选）

## 常见问题

### Q: 无法上传大文件？
A: 默认 Flask 没有文件大小限制。如果使用 Nginx，需要配置 `client_max_body_size`。

### Q: 如何修改默认端口？
A: 编辑 `app.py` 最后一行，将 `port=5000` 改为其他端口。

### Q: 如何限制访问 IP？
A: 在 Nginx 配置中添加 IP 白名单，或使用防火墙规则。

### Q: 支持中文文件名吗？
A: 完全支持中文文件名和文件夹名。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 免责声明

本软件按"原样"提供，不提供任何明示或暗示的保证。使用本软件造成的任何数据丢失或损坏，作者不承担任何责任。

请务必：
- 仅在受信任的网络中使用
- 定期备份重要数据
- 谨慎执行删除操作
