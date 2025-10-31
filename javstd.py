import logging
import os
import xml.etree.ElementTree as ET
from subtitle_scraper import subtitle_handler, is_video_file

CONFIG = {
    "default": {
        "logging": {
            "filename": "javstd.log",
            "level": "INFO"
        }
    },
    "webhook": {
        "custom": {
            "url": "http://127.0.0.1/webhook/common",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer 123456"
            },
            "timeout": 30
        }
    },
    "javstd": {
        "src_path": "\\\\NAS\\av",
        "save_path": "\\\\NAS\\jav_subtitle"
    }
}

# 配置日志写入文件和控制台
def setup_logging():
    # 从配置中获取日志设置
    logging_config = CONFIG.get("default", {}).get("logging", {})
    log_filename = logging_config.get("filename", "javstd.log")
    log_level = logging_config.get("level", "INFO")
    level = getattr(logging, log_level, logging.INFO)
    
    # 获取脚本所在目录
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 将日志文件名转换为绝对路径（放在脚本同级目录）
    if not os.path.isabs(log_filename):
        log_filename = os.path.join(_script_dir, log_filename)
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    
    # 获取脚本名称
    script_name = __file__.split('/')[-1].split('.')[0] if '/' in __file__ else __file__.split('\\')[-1].split('.')[0]
    
    # 创建文件和控制台处理器
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    console_handler = logging.StreamHandler()
    file_handler.setLevel(level)
    console_handler.setLevel(level)
    
    # 设置日志格式，包含脚本名称
    formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - {script_name} - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 配置logger
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def send_webhook_to_custom(title: str, detail: str, tag: str = None, from_: str = None, level: str = 'info', adult: bool = False) -> bool:
    """发送消息到自定义webhook"""
    try:
        import requests
        # 从配置中获取自定义webhook配置
        custom_webhook = CONFIG.get('webhook', {}).get('custom', {})
        
        # 兼容两种配置格式：单个webhook字典 或 webhook列表
        if not custom_webhook:
            logger.error("自定义webhook未配置")
            return False
        
        success_count = 0
        webhook_url = custom_webhook.get('url')
        if not webhook_url:
                logger.error("自定义webhook URL未配置")
                return False

        headers = custom_webhook.get('headers', {})
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        # 检查参数配置，并设置默认值，title 和 detail 必须存在一个
        if not title and not detail:
            logger.error("自定义webhook消息标题和详情不能同时为空")
            return False
        if not tag:
            tag = ''
        if not from_:
            from_ = ''
        
        # 填充消息内容
        body = {
            'msg_type': 'markdown',
            'content': {
                'title': title,
                'detail': detail,
                'from': from_,
                'tag': tag,
                'level': level,
                'adult': adult
            }
        }
            
        # 发送POST请求
        logger.info(f'发送消息到自定义webhook: {webhook_url}')
        timeout = custom_webhook.get('timeout', 10)
        response = requests.post(webhook_url, headers=headers, json=body, timeout=timeout)
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f'自定义webhook消息发送成功: {webhook_url}')
            success_count += 1
        else:
            logger.error(f'自定义webhook消息发送失败: {webhook_url}, 状态码: {response.status_code}, 响应: {response.text}')
        
        return success_count > 0
    except Exception as e:
        logger.exception(f'自定义webhook消息发送异常: {str(e)}')
        return False

def extract_info_from_nfo(nfo_path):
    """
    从nfo文件中提取num字段值和中文字幕信息
    :param nfo_path: nfo文件的路径
    :return: tuple(num字段值, 是否有中文字幕)，如果未找到num则返回(None, False)
    """
    try:
        # 解析XML文件
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        
        # 查找num标签
        num_element = root.find('num')
        num_value = num_element.text if num_element is not None else None
        
        # 检查是否有中文字幕标签
        has_chinese_subtitle = False
        
        # 查找<tag>元素中的中文字幕
        for tag_element in root.findall('.//tag'):
            if tag_element.text == '中文字幕':
                has_chinese_subtitle = True
                break
                
        # 如果没在<tag>中找到，也在<genre>中查找
        if not has_chinese_subtitle:
            for genre_element in root.findall('.//genre'):
                if genre_element.text == '中文字幕':
                    has_chinese_subtitle = True
                    break
        
        return num_value, has_chinese_subtitle
    except ET.ParseError as e:
        print(f"Error parsing XML file {nfo_path}: {e}")
        return None, False
    except FileNotFoundError:
        print(f"NFO file not found: {nfo_path}")
        return None, False
    except Exception as e:
        print(f"Error reading NFO file {nfo_path}: {e}")
        return None, False


def main():
    # 初始化日志配置
    logger = setup_logging()
    logger.info("脚本开始执行")
    # 从配置中获取src_path和save_path
    src_path = CONFIG.get("javstd", {}).get("src_path")
    save_path = CONFIG.get("javstd", {}).get("save_path")
    if not src_path or not save_path:
        logger.error("src_path或save_path未配置")
        return

    # 递归遍历src_path的所有视频文件
    for root, dirs, files in os.walk(src_path):
        for filename in files:
            if not is_video_file(filename):
                continue

            # 跳过处理含trailer的视频
            if 'trailer' in filename.lower():
                continue
            
            # 跳过处理已有中文字幕的视频
            if '-C' in filename:
                logger.debug(f"跳过处理已有中文字幕的视频: {filename}")
                continue
            
            logger.info(f"处理视频文件: {os.path.join(root, filename)}")

            # 从src_path中的nfo文件提取num字段值和中文字幕信息
            nfo_path = os.path.join(root, filename.replace('.mp4', '.nfo').replace('.avi', '.nfo').replace('.mkv', '.nfo'))
            jav_number, has_chinese_subtitle = extract_info_from_nfo(nfo_path)
            if not jav_number:
                logger.warning(f"无法从NFO文件中提取jav_number字段值: {filename}")
                continue
            logger.info(f"从NFO文件中提取到jav_number: {jav_number}")
            
            # 如果NFO文件中标记了有中文字幕，跳过处理
            if has_chinese_subtitle:
                logger.debug(f"NFO文件标记已有中文字幕，跳过处理: {filename}")
                continue

            # 如果字幕库中已存在字幕文件，跳过处理
            subtitle_path = os.path.join(save_path, f"{jav_number}.srt" or f"{jav_number}.ass")
            if os.path.exists(subtitle_path):
                logger.debug(f"字幕文件已存在，跳过处理: {subtitle_path}")
                continue

            # 调用subtitle_handler处理字幕
            logger.info(f"尝试获取 {jav_number} 的字幕")
            try:
                results = subtitle_handler(jav_number, save_path=save_path)
                # 我们传入的是jav_number，因此有且仅有一条结果
                if results[0]['success']:
                    result_path = results[0].get('path', '')
                    logger.info(f"成功获取字幕: {result_path}")
                    
                    # 重命名下载的字幕文件，将*.zh-CN.srt重命名为*.srt
                    if result_path.endswith('.zh-CN.srt'):
                        new_path = result_path.rsplit('.', 2)[0] + '.srt'
                        os.rename(result_path, new_path)
                        logger.info(f"最终保存字幕文件: {new_path}")
                    else:
                        logger.info(f"最终保存字幕文件: {result_path}")
                else:
                    logger.error(f"处理失败: {results[0].get('error', '')}")
            except Exception as e:
                logger.error(f"处理失败: {str(e)}")


    logger.info("脚本执行完成\n")

if __name__ == "__main__":
    main()