import os
import shutil
from typing import List, Dict, Any

def get_folder_tree(base_dir: str) -> List[Dict[str, Any]]:
    """递归获取整个输出目录下的文件夹树形结构"""
    if not os.path.exists(base_dir):
        return []
        
    def _build_tree(current_dir: str) -> List[Dict[str, Any]]:
        nodes = []
        try:
            items = os.listdir(current_dir)
        except OSError:
            return []
            
        # 排序：按照修改时间或名称排序
        items.sort(key=lambda x: os.path.getmtime(os.path.join(current_dir, x)) if os.path.exists(os.path.join(current_dir, x)) else 0, reverse=True)
        
        for item in items:
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                # 递归获取子目录
                children = _build_tree(item_path)
                # 计算相对基本目录的路径，作为前端标识用的 id
                rel_path = os.path.relpath(item_path, base_dir).replace('\\', '/')
                nodes.append({
                    "id": rel_path,
                    "name": item,
                    "children": children
                })
        return nodes

    return _build_tree(base_dir)

def create_nested_folder(base_dir: str, parent_rel_path: str, new_folder_name: str) -> dict:
    """在指定相对路径下创建一个子文件夹"""
    # 防止跳出 base_dir
    parent_rel_path = parent_rel_path.lstrip('/')
    if '..' in parent_rel_path or '..' in new_folder_name:
        return {"status": "error", "message": "非法路径"}
        
    target_dir = os.path.join(base_dir, parent_rel_path, new_folder_name) if parent_rel_path else os.path.join(base_dir, new_folder_name)
    
    if os.path.exists(target_dir):
        return {"status": "error", "message": "文件夹已存在"}
        
    try:
        os.makedirs(target_dir, exist_ok=True)
        return {"status": "success", "message": "创建成功"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def rename_folder(base_dir: str, target_rel_path: str, new_name: str) -> dict:
    """重命名指定的文件夹"""
    target_rel_path = target_rel_path.lstrip('/')
    if '..' in target_rel_path or '..' in new_name or not target_rel_path:
        return {"status": "error", "message": "非法路径"}
        
    old_path = os.path.join(base_dir, target_rel_path)
    parent_dir = os.path.dirname(old_path)
    new_path = os.path.join(parent_dir, new_name)
    
    if not os.path.exists(old_path):
        return {"status": "error", "message": "目标不存在"}
        
    if os.path.exists(new_path):
        return {"status": "error", "message": "新名称已存在"}
        
    try:
        os.rename(old_path, new_path)
        return {"status": "success", "message": "重命名成功"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_folder(base_dir: str, target_rel_path: str) -> dict:
    """删除指定的文件夹极其内容"""
    target_rel_path = target_rel_path.lstrip('/')
    if '..' in target_rel_path or not target_rel_path:
        return {"status": "error", "message": "非法路径"}
        
    target_path = os.path.join(base_dir, target_rel_path)
    if not os.path.exists(target_path):
        return {"status": "error", "message": "目标不存在"}
        
    try:
        shutil.rmtree(target_path)
        return {"status": "success", "message": "删除成功"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_session_texts_nested(base_dir: str, target_rel_path: str) -> List[str]:
    """读取指定嵌套路径下所有 result.txt 中的文本内容"""
    target_rel_path = target_rel_path.lstrip('/')
    if '..' in target_rel_path:
         return []
         
    session_dir = os.path.join(base_dir, target_rel_path)
    if not os.path.exists(session_dir):
        return []
        
    texts = []
    # 获取所有的内部单次录音 segment (它们是由 create_segment_folder 自动创建的，通常以时间戳开头)
    segments = []
    for d in os.listdir(session_dir):
        seg_dir = os.path.join(session_dir, d)
        if os.path.isdir(seg_dir):
            segments.append(seg_dir)
            
    # 按字母序（通常就是时间戳序）排列
    segments.sort()
    for seg in segments:
        txt_path = os.path.join(seg, "result.txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    texts.append(content)
                
    return texts
