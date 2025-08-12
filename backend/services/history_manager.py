"""
对话历史管理服务
"""

from pathlib import Path
from typing import List, Dict, Any
from common.utils import load_conversation_history


def get_conversation_history(script_name: str) -> Dict[str, Any]:
    """
    获取指定脚本的对话历史
    
    Args:
        script_name: 脚本名称
        
    Returns:
        包含历史记录的字典
    """
    try:
        history_records = load_conversation_history(script_name)
        
        # 格式化历史记录为前端需要的格式
        formatted_records = []
        for record in history_records:
            formatted_record = {
                "id": record.get("timestamp", ""),
                "timestamp": record.get("timestamp", ""),
                "script_name": record.get("script_name", ""),
                "prompt": record.get("prompt", ""),
                "message_count": record.get("message_count", 0),
                "messages": record.get("messages", []),
                "display_name": format_display_name(record),
                "relative_path": record.get("relative_path", "")
            }
            formatted_records.append(formatted_record)
        
        return {
            "success": True,
            "script_name": script_name,
            "total_records": len(formatted_records),
            "records": formatted_records
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "script_name": script_name,
            "total_records": 0,
            "records": []
        }


def format_display_name(record: Dict[str, Any]) -> str:
    """
    格式化显示名称
    
    Args:
        record: 历史记录
        
    Returns:
        格式化的显示名称
    """
    timestamp = record.get("timestamp", "")
    message_count = record.get("message_count", 0)
    
    if timestamp:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            return f"{formatted_time} ({message_count} messages)"
        except:
            pass
    
    return f"Unknown time ({message_count} messages)"


def get_all_script_histories() -> Dict[str, Any]:
    """
    获取所有脚本的历史记录概览
    
    Returns:
        包含所有脚本历史概览的字典
    """
    try:
        base_dir = Path.cwd()
        history_base_dir = base_dir / "static" / "history"
        
        if not history_base_dir.exists():
            return {
                "success": True,
                "scripts": {}
            }
        
        scripts_overview = {}
        
        # 遍历所有脚本目录
        for script_dir in history_base_dir.iterdir():
            if not script_dir.is_dir():
                continue
                
            script_name = script_dir.name
            history_records = load_conversation_history(script_name)
            
            if history_records:
                scripts_overview[script_name] = {
                    "total_records": len(history_records),
                    "latest_timestamp": history_records[0].get("timestamp", "") if history_records else "",
                    "latest_display_name": format_display_name(history_records[0]) if history_records else ""
                }
        
        return {
            "success": True,
            "scripts": scripts_overview
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "scripts": {}
        }


def delete_conversation_history(script_name: str, timestamp: str = None) -> Dict[str, Any]:
    """
    删除对话历史
    
    Args:
        script_name: 脚本名称
        timestamp: 时间戳，如果为 None 则删除所有历史
        
    Returns:
        删除结果
    """
    try:
        base_dir = Path.cwd()
        
        if timestamp:
            # 删除特定的历史记录
            history_records = load_conversation_history(script_name)
            target_record = None
            
            for record in history_records:
                if record.get("timestamp") == timestamp:
                    target_record = record
                    break
            
            if target_record:
                file_path = Path(target_record["file_path"])
                if file_path.exists():
                    file_path.unlink()
                    return {
                        "success": True,
                        "message": f"Deleted history record: {timestamp}"
                    }
                else:
                    return {
                        "success": False,
                        "error": "History file not found"
                    }
            else:
                return {
                    "success": False,
                    "error": "History record not found"
                }
        else:
            # 删除所有历史记录
            script_history_dir = base_dir / "static" / "history" / script_name
            if script_history_dir.exists():
                import shutil
                shutil.rmtree(script_history_dir)
                return {
                    "success": True,
                    "message": f"Deleted all history for script: {script_name}"
                }
            else:
                return {
                    "success": False,
                    "error": "No history found for this script"
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
