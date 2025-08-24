import os
import json
from typing import List, Dict, Any
import base64
from http import HTTPStatus
from dashscope import Application


def encode_image_to_base64(image_path: str) -> str:
    """
    将图片文件编码为base64字符串
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        base64编码的字符串
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_files_with_dashscope(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    使用阿里百炼大模型API分析文件并获取结构化内容
    
    Args:
        file_paths: 文件路径列表
        
    Returns:
        结构化的单词数据列表
    """
    # 获取API密钥和应用ID
    api_key = get_api_key()
    app_id = os.environ.get("DASHSCOPE_APP_ID")
    
    if not api_key:
        print("错误: 未设置DASHSCOPE_API_KEY环境变量")
        return []
    
    if not app_id:
        print("错误: 未设置DASHSCOPE_APP_ID环境变量")
        return []
    
    # 构造提示词
    prompt = "请分析这些文件中的内容，提取其中的英文单词、中文释义、词性和例句，以JSON格式返回。"
    prompt += "格式示例: [{\"english\": \"word\", \"chinese\": \"中文释义\", \"part_of_speech\": \"词性\", \"example_sentence\": \"例句\"}]"
    
    # 调用阿里百炼大模型API
    print("调用阿里百炼大模型API分析文件:")
    for file_path in file_paths:
        print(f"  - {file_path}")
    
    print("正在分析文件内容...")
    
    try:
        response = Application.call(
            api_key=api_key,
            app_id=app_id,
            prompt=prompt
        )
        
        if response.status_code != HTTPStatus.OK:
            print(f'request_id={response.request_id}')
            print(f'code={response.status_code}')
            print(f'message={response.message}')
            print('请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
            return []
        else:
            # 解析响应内容
            result_text = response.output.text
            print("分析完成，获取到结构化数据")
            
            # 这里应该解析返回的JSON数据
            # 暂时返回示例数据
            sample_data = [
                {
                    "english": "Hello",
                    "chinese": "你好",
                    "part_of_speech": "interjection",
                    "example_sentence": "Hello! How are you today?"
                },
                {
                    "english": "World",
                    "chinese": "世界",
                    "part_of_speech": "noun",
                    "example_sentence": "The whole world was watching."
                }
            ]
            
            return sample_data
    except Exception as e:
        print(f"调用阿里百炼大模型API时发生错误: {e}")
        return []


def get_api_key() -> str:
    """
    获取DashScope API密钥
    
    Returns:
        API密钥字符串
    """
    # 从环境变量获取API密钥
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    
    if not api_key:
        print("警告: 未设置DASHSCOPE_API_KEY环境变量")
        print("请设置环境变量，例如: export DASHSCOPE_API_KEY=your_api_key_here")
    
    return api_key