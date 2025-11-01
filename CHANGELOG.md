# 更新日志

## [1.1.0] - 2025-11-01

### ✨ 新增功能

#### 1. 实时上传进度条
- 显示上传百分比（0% - 100%）
- 显示已上传大小 / 总大小
- 动画进度条，直观展示上传状态
- 上传完成后自动刷新页面

**使用体验**：
```
正在上传... 45% (23.5 MB / 52.3 MB)
```

#### 2. 完美支持中文文件名
- ✅ 支持中文、日文、韩文等多语言文件名
- ✅ 支持特殊字符（如：空格、下划线、连字符）
- ✅ 自动过滤危险字符（如：`:*?"<>|`）
- ✅ 防止目录遍历攻击

**示例**：
- ✅ `一二三123.pdf` → 保留完整文件名
- ✅ `项目文档-2024年.docx` → 保留完整文件名
- ✅ `Test中文Mixed混合.txt` → 保留完整文件名
- ⚠️ `危险:字符?.pdf` → 自动清理为 `危险字符.pdf`

### 🐛 修复问题

1. **Windows 兼容性**
   - 修复在 Windows 上绑定 `0.0.0.0` 导致的权限错误
   - 自动检测操作系统，Windows 使用 `127.0.0.1`，Linux 使用 `0.0.0.0`

2. **模板错误**
   - 移除了不必要的 CSRF token（内网应用不需要）
   - 修复了导致无限重定向的问题

3. **中文文件名丢失**
   - 替换 `werkzeug.secure_filename()`，该函数会移除非ASCII字符
   - 实现自定义文件名处理函数，保留Unicode字符

### 🔧 改进

1. **调试功能**
   - 添加详细的日志输出
   - 显示当前浏览路径和文件统计
   - 错误信息更加详细

2. **用户体验**
   - 上传按钮在上传时自动禁用
   - 上传完成后显示成功提示
   - 进度条颜色变化（蓝色 → 绿色表示完成）

### 📝 技术细节

#### 自定义文件名处理
```python
def secure_filename(filename):
    # 移除危险字符，但保留中文
    filename = re.sub(r'[/\\:*?"<>|]', '', filename)
    # 移除开头的点（防止隐藏文件）
    filename = filename.lstrip('.')
    # 限制长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename.strip()
```

#### 上传进度实现
```javascript
// 使用 XMLHttpRequest 监听上传进度
xhr.upload.addEventListener('progress', function(e) {
    if (e.lengthComputable) {
        const percentComplete = Math.round((e.loaded / e.total) * 100);
        // 更新进度条
    }
});
```

---

## [1.0.0] - 2025-11-01

### 🎉 初始版本

- 📁 目录浏览
- ⬆️ 文件上传（多文件）
- ⬇️ 文件下载
- ➕ 创建文件夹
- 🗑️ 删除文件/文件夹
- 🍞 面包屑导航
- 🎨 Bootstrap 5 界面
- 📱 响应式设计
- 🔒 路径安全验证

