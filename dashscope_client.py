import os
import json
from typing import List, Dict, Any
from http import HTTPStatus
import dashscope


def analyze_file_with_dashscope(file_path: str) -> List[Dict[str, Any]]:
    """
    使用阿里云百炼大模型API分析文件中的内容，提取单词信息

    Args:
        file_path: 文件路径

    Returns:
        解析后的单词数据列表
    """
    # 从环境变量获取API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

    dashscope.api_key = api_key

    # 构造提示词，要求模型以特定格式返回单词数据
    prompt = """请分析图片中的内容，提取出英文单词及其相关信息。
    对于每个识别出的单词，请按照以下JSON格式返回：
    {
        "word": "单词",
        "phonetic": "音标",
        "meaning": "中文含义"
    }
    
    请将所有单词以数组形式返回，格式如下：
    [
        {
            "word": "example",
            "phonetic": "/ɪɡˈzæmpəl/",
            "meaning": "例子"
        }
    ]
    
    只返回JSON格式数据，不要包含其他文字。"""

    # 调用多模态模型处理文件
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "text": "你是一个专业的英语老师，擅长识别图片中的英文单词并提供详细解释。"
                }
            ],
        },
        {"role": "user", "content": []},
    ]

    # 添加文件内容到消息中
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in [".jpeg", ".jpg"]:
        messages[1]["content"].append(
            {"image": f"file://{os.path.abspath(file_path)}"}
        )
    elif file_ext == ".pdf":
        # 对于PDF文件，需要先处理或提示用户不支持
        print(f"警告: 当前版本可能不完全支持PDF文件: {file_path}")
        # 这里可以添加PDF处理逻辑，暂时跳过
        return []

    messages[1]["content"].append({"text": prompt})

    # 调用DashScope API
    response = dashscope.MultiModalConversation.call(
        model="qwen-vl-max", messages=messages
    )

    # 处理响应
    if response.status_code == HTTPStatus.OK:
        try:
            # 从响应中提取文本内容
            text_content = response.output.choices[0].message.content
            # 如果返回的是列表格式，直接使用
            if isinstance(text_content, list):
                # 提取文本部分
                for item in text_content:
                    if item.get("text"):
                        # 尝试解析JSON
                        data = json.loads(item["text"])
                        if isinstance(data, list):
                            return data
            else:
                # 如果是字符串，尝试解析JSON
                # 需要从文本中提取JSON部分
                json_str = extract_json_from_text(text_content)
                if json_str:
                    return json.loads(json_str)

            # 如果以上都不成功，返回空列表
            return []
        except Exception as e:
            print(f"解析API响应时出错: {e}")
            return []
    else:
        print(f"API调用失败: {response.code} - {response.message}")
        return []


def extract_json_from_text(text):
    """
    从文本中提取JSON字符串

    Args:
        text: 包含JSON的文本

    Returns:
        提取出的JSON字符串，如果未找到则返回None
    """
    # 查找第一个[和最后一个]之间的内容
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1 and start < end:
        json_str = text[start : end + 1]
        try:
            # 验证是否为有效的JSON
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass

    return None