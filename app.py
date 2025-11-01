#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web 文件浏览器
用于在阿里云函数计算 FC 中管理 NAS 文件系统
警告：此应用不包含认证机制，仅限内网使用！
"""
# 阿里云fc层搭建环境，勿删
import sys
sys.path.append('/opt/python')
# import {PackageFromLayer}
import os
import shutil
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, abort
from werkzeug.utils import secure_filename as werkzeug_secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 配置根目录，默认为 /mnt/nas，可通过环境变量覆盖
BASE_DIR = os.environ.get('BASE_DIR', '/mnt/nas')
BASE_DIR = os.path.abspath(BASE_DIR)

# 如果 BASE_DIR 不存在，创建它（开发环境）
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR, exist_ok=True)


def secure_filename(filename):
    """
    自定义文件名安全处理，支持中文字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        安全的文件名
    """
    # 移除路径分隔符和其他危险字符，但保留中文、字母、数字、点、下划线、连字符
    filename = re.sub(r'[/\\:*?"<>|]', '', filename)
    
    # 移除开头的点（防止隐藏文件）
    filename = filename.lstrip('.')
    
    # 如果文件名为空或只有空格，使用默认名称
    if not filename or filename.isspace():
        return 'unnamed_file'
    
    # 限制文件名长度（防止过长的文件名）
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename.strip()


def safe_join(base, *paths):
    """
    安全地拼接路径，防止目录遍历攻击
    
    Args:
        base: 基础目录路径
        *paths: 要拼接的路径部分
    
    Returns:
        安全的绝对路径
    
    Raises:
        ValueError: 如果结果路径不在基础目录内
    """
    # 拼接路径
    path = os.path.join(base, *paths)
    # 解析为真实路径（处理符号链接和 ..）
    real_path = os.path.abspath(os.path.realpath(path))
    real_base = os.path.abspath(os.path.realpath(base))
    
    # 确保结果路径在基础目录内
    if not real_path.startswith(real_base):
        raise ValueError("路径不安全，禁止访问")
    
    return real_path


def format_size(size_bytes):
    """
    将字节数格式化为人类可读的格式
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化后的字符串，如 "1.23 MB"
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def get_file_type(filename):
    """
    根据文件扩展名判断文件类型，用于显示对应图标
    
    Args:
        filename: 文件名
    
    Returns:
        文件类型字符串
    """
    ext = os.path.splitext(filename)[1].lower()
    
    # 图片文件
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico']:
        return 'image'
    # 视频文件
    elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
        return 'video'
    # 音频文件
    elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']:
        return 'audio'
    # 文档文件
    elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md']:
        return 'document'
    # 压缩文件
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz']:
        return 'archive'
    # 代码文件
    elif ext in ['.py', '.js', '.java', '.c', '.cpp', '.h', '.html', '.css', '.php', '.go', '.rs']:
        return 'code'
    else:
        return 'file'


def get_directory_contents(path):
    """
    获取目录内容，分别返回文件夹和文件列表
    
    Args:
        path: 目录路径
    
    Returns:
        包含文件夹和文件信息的元组 (folders, files)
    """
    folders = []
    files = []
    
    try:
        items = os.listdir(path)
    except PermissionError:
        flash('没有权限访问此目录', 'danger')
        return folders, files
    
    for item in items:
        item_path = os.path.join(path, item)
        
        try:
            stat = os.stat(item_path)
            modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            if os.path.isdir(item_path):
                folders.append({
                    'name': item,
                    'modified': modified_time,
                    'type': 'folder'
                })
            else:
                files.append({
                    'name': item,
                    'size': stat.st_size,
                    'size_formatted': format_size(stat.st_size),
                    'modified': modified_time,
                    'type': get_file_type(item)
                })
        except (OSError, PermissionError):
            # 跳过无法访问的文件
            continue
    
    # 排序：文件夹按名称排序，文件按名称排序
    folders.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())
    
    return folders, files


def get_breadcrumbs(subpath):
    """
    生成面包屑导航数据
    
    Args:
        subpath: 当前子路径
    
    Returns:
        面包屑列表，每项包含 name 和 path
    """
    breadcrumbs = [{'name': '根目录', 'path': ''}]
    
    if subpath:
        parts = subpath.split('/')
        current_path = ''
        for part in parts:
            if part:
                current_path = f"{current_path}/{part}" if current_path else part
                breadcrumbs.append({'name': part, 'path': current_path})
    
    return breadcrumbs


@app.route('/')
def index():
    """首页，重定向到浏览页面"""
    return redirect(url_for('browse', subpath=''))


@app.route('/browse/', defaults={'subpath': ''})
@app.route('/browse/<path:subpath>')
def browse(subpath):
    """
    浏览目录内容
    
    Args:
        subpath: 子路径
    """
    # 防止重定向循环 - 如果已经在处理根路径且出错，直接显示错误
    if subpath == '' and request.args.get('_error'):
        return "应用配置错误，请检查 BASE_DIR 路径和模板文件", 500
    
    try:
        # 获取安全路径
        current_path = safe_join(BASE_DIR, subpath)
        
        print(f"[DEBUG] Browsing: {current_path}")
        
        # 检查路径是否存在
        if not os.path.exists(current_path):
            print(f"[ERROR] Path does not exist: {current_path}")
            abort(404)
        
        # 如果是文件，重定向到下载
        if os.path.isfile(current_path):
            return redirect(url_for('download', filepath=subpath))
        
        # 获取目录内容
        folders, files = get_directory_contents(current_path)
        print(f"[DEBUG] Found {len(folders)} folders and {len(files)} files")
        
        # 生成面包屑导航
        breadcrumbs = get_breadcrumbs(subpath)
        
        return render_template(
            'index.html',
            folders=folders,
            files=files,
            current_path=subpath,
            breadcrumbs=breadcrumbs
        )
    
    except ValueError as e:
        print(f"[ERROR] ValueError in browse: {e}")
        if subpath == '':
            return f"路径安全验证失败: {e}", 500
        flash('不允许访问此路径', 'danger')
        return redirect(url_for('browse', subpath='', _error='1'))
    except Exception as e:
        print(f"[ERROR] Exception in browse: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        if subpath == '':
            return f"应用错误: {e}", 500
        flash(f'发生错误：{str(e)}', 'danger')
        return redirect(url_for('browse', subpath='', _error='1'))


@app.route('/download/<path:filepath>')
def download(filepath):
    """
    下载文件
    
    Args:
        filepath: 文件路径
    """
    try:
        # 获取安全路径
        file_path = safe_join(BASE_DIR, filepath)
        
        # 检查文件是否存在
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            abort(404)
        
        # 发送文件
        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
    
    except ValueError:
        abort(403)
    except Exception as e:
        flash(f'下载失败：{str(e)}', 'danger')
        return redirect(url_for('browse', subpath=''))


@app.route('/upload/', defaults={'subpath': ''}, methods=['POST'])
@app.route('/upload/<path:subpath>', methods=['POST'])
def upload(subpath):
    """
    上传文件
    
    Args:
        subpath: 目标子路径
    """
    try:
        # 获取安全路径
        target_path = safe_join(BASE_DIR, subpath)
        
        # 检查目录是否存在
        if not os.path.exists(target_path) or not os.path.isdir(target_path):
            flash('目标目录不存在', 'danger')
            return redirect(url_for('browse', subpath=subpath))
        
        # 获取上传的文件列表
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            flash('请选择要上传的文件', 'warning')
            return redirect(url_for('browse', subpath=subpath))
        
        uploaded_count = 0
        for file in files:
            if file and file.filename:
                # 使用 secure_filename 处理文件名
                filename = secure_filename(file.filename)
                if not filename:
                    continue
                
                file_path = os.path.join(target_path, filename)
                
                # 如果文件已存在，添加数字后缀
                if os.path.exists(file_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(file_path):
                        filename = f"{base}_{counter}{ext}"
                        file_path = os.path.join(target_path, filename)
                        counter += 1
                
                file.save(file_path)
                uploaded_count += 1
        
        flash(f'成功上传 {uploaded_count} 个文件', 'success')
        return redirect(url_for('browse', subpath=subpath))
    
    except ValueError:
        flash('不允许访问此路径', 'danger')
        return redirect(url_for('browse', subpath=''))
    except Exception as e:
        flash(f'上传失败：{str(e)}', 'danger')
        return redirect(url_for('browse', subpath=subpath))


@app.route('/create-folder/', defaults={'subpath': ''}, methods=['POST'])
@app.route('/create-folder/<path:subpath>', methods=['POST'])
def create_folder(subpath):
    """
    创建文件夹
    
    Args:
        subpath: 当前子路径
    """
    try:
        # 获取安全路径
        current_path = safe_join(BASE_DIR, subpath)
        
        # 检查目录是否存在
        if not os.path.exists(current_path) or not os.path.isdir(current_path):
            flash('当前目录不存在', 'danger')
            return redirect(url_for('browse', subpath=subpath))
        
        # 获取文件夹名称
        folder_name = request.form.get('folder_name', '').strip()
        
        if not folder_name:
            flash('请输入文件夹名称', 'warning')
            return redirect(url_for('browse', subpath=subpath))
        
        # 使用 secure_filename 处理文件夹名
        folder_name = secure_filename(folder_name)
        
        if not folder_name:
            flash('文件夹名称无效', 'danger')
            return redirect(url_for('browse', subpath=subpath))
        
        new_folder_path = os.path.join(current_path, folder_name)
        
        # 检查是否已存在
        if os.path.exists(new_folder_path):
            flash(f'文件夹 "{folder_name}" 已存在', 'warning')
            return redirect(url_for('browse', subpath=subpath))
        
        # 创建文件夹
        os.makedirs(new_folder_path)
        flash(f'成功创建文件夹 "{folder_name}"', 'success')
        return redirect(url_for('browse', subpath=subpath))
    
    except ValueError:
        flash('不允许访问此路径', 'danger')
        return redirect(url_for('browse', subpath=''))
    except Exception as e:
        flash(f'创建文件夹失败：{str(e)}', 'danger')
        return redirect(url_for('browse', subpath=subpath))


@app.route('/delete/<path:filepath>', methods=['POST'])
def delete(filepath):
    """
    删除文件或文件夹
    
    Args:
        filepath: 文件或文件夹路径
    """
    try:
        # 获取安全路径
        target_path = safe_join(BASE_DIR, filepath)
        
        # 检查是否存在
        if not os.path.exists(target_path):
            flash('文件或文件夹不存在', 'warning')
            return redirect(request.referrer or url_for('browse', subpath=''))
        
        # 获取父目录路径（用于重定向）
        parent_path = os.path.dirname(filepath)
        
        # 删除文件或文件夹
        if os.path.isfile(target_path):
            os.remove(target_path)
            flash(f'成功删除文件', 'success')
        elif os.path.isdir(target_path):
            shutil.rmtree(target_path)
            flash(f'成功删除文件夹', 'success')
        
        return redirect(url_for('browse', subpath=parent_path))
    
    except ValueError:
        flash('不允许访问此路径', 'danger')
        return redirect(url_for('browse', subpath=''))
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'danger')
        return redirect(request.referrer or url_for('browse', subpath=''))


@app.errorhandler(404)
def not_found(e):
    """404 错误处理"""
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    """403 错误处理"""
    flash('禁止访问', 'danger')
    return redirect(url_for('browse', subpath=''))


@app.errorhandler(500)
def internal_error(e):
    """500 错误处理"""
    flash('服务器内部错误', 'danger')
    return redirect(url_for('browse', subpath=''))


if __name__ == '__main__':
    # 开发模式运行
    # 在 Windows 上使用 127.0.0.1，在 Linux 上可以使用 0.0.0.0
    import platform
    host = '127.0.0.1' if platform.system() == 'Windows' else '0.0.0.0'
    port = 5001
    
    print(f"Flask Web 文件浏览器启动中...")
    print(f"根目录: {BASE_DIR}")
    print(f"警告：此应用不包含认证机制，仅限内网使用！")
    print(f"访问地址: http://{host}:{port}")
    if platform.system() == 'Windows':
        print(f"局域网访问: http://<本机IP>:{port}")
    
    app.run(host=host, port=port, debug=True)

