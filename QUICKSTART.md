# Flask NAS 文件浏览器 - 快速开始指南

## 🚀 快速开始（5 分钟部署）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

### 3. 访问应用

打开浏览器访问：`http://localhost:5000`

就是这么简单！

---

## 📝 环境变量配置（可选）

### 自定义根目录

```bash
# Linux/Mac
export BASE_DIR="/your/custom/path"
python app.py

# Windows
set BASE_DIR="D:\your\custom\path"
python app.py
```

### 自定义端口

编辑 `app.py` 最后一行：

```python
app.run(host='0.0.0.0', port=8080, debug=True)  # 改为 8080 端口
```

---

## 🎯 核心功能演示

### 浏览文件
- 点击文件夹 → 进入子目录
- 点击面包屑 → 返回上级目录

### 上传文件
1. 点击"选择文件"
2. 选择一个或多个文件（支持中文文件名 ✨）
3. 点击"上传文件"
4. 查看实时进度条 📊

### 下载文件
- 点击文件名 → 自动下载

### 创建文件夹
1. 输入文件夹名称
2. 点击"创建文件夹"

### 删除文件/文件夹
1. 点击"删除"按钮
2. 确认操作

---

## 🏭 生产环境部署

### 使用 Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 使用 systemd（推荐）

创建 `/etc/systemd/system/flask-nas.service`：

```ini
[Unit]
Description=Flask NAS File Browser
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/fc_flask_nas
Environment="BASE_DIR=/mnt/nas"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl start flask-nas
sudo systemctl enable flask-nas
```

---

## ⚠️ 安全提醒

**此应用不包含认证机制，仅限内网使用！**

- ✅ 家庭局域网
- ✅ 公司内网
- ✅ VPN 访问
- ❌ 公共互联网

---

## 🐛 常见问题

### Q: 无法上传大文件？
A: 默认无限制。如果使用 Nginx，需配置 `client_max_body_size`。

### Q: 如何限制访问 IP？
A: 在 Nginx 或防火墙中配置 IP 白名单。

### Q: 支持中文文件名吗？
A: 完全支持。

---

## 📞 需要帮助？

查看完整文档：[README.md](README.md)

