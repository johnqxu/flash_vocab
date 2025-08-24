import hashlib
import os
import json
from typing import List, Dict, Any
from http import HTTPStatus
import dashscope
from alibabacloud_bailian20231229.client import Client as bailian20231229Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_bailian20231229.models import ApplyFileUploadLeaseResponse
import requests
from urllib.parse import urlparse


def analyze_file_with_dashscope(file_path: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")
    dashscope.api_key = api_key
    lease: ApplyFileUploadLeaseResponse = create_upload_lease(file_path)
    upload_file(
        lease.body.data.param.url,
        lease.body.data.param.headers["X-bailian-extra"],
        lease.body.data.param.headers["Content-Type"],
        file_path,
    )


def create_client() -> bailian20231229Client:
    credential = CredentialClient()
    config = open_api_models.Config(
        type="access_key",
        access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    )
    config.endpoint = f"bailian.cn-beijing.aliyuncs.com"
    return bailian20231229Client(config)


def calculate_md5(file_path):
    """计算文档的 MD5 值。

    Args:
        file_path (str): 文档的路径。

    Returns:
        str: 文档的 MD5 值。
    """
    md5_hash = hashlib.md5()
    # 以二进制形式读取文件
    with open(file_path, "rb") as f:
        # 按块读取文件，避免大文件占用过多内存
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def create_upload_lease(file_path: str) -> Dict[str, Any]:
    file_name = os.path.basename(file_path)

    client = create_client()
    apply_file_upload_lease_request = (
        bailian_20231229_models.ApplyFileUploadLeaseRequest(
            md_5=calculate_md5(file_path),
            file_name=file_name,
            size_in_bytes=os.path.getsize(file_path),
        )
    )
    runtime = util_models.RuntimeOptions(read_timeout=6000, connect_timeout=6000)
    headers = {}
    try:
        resp = client.apply_file_upload_lease_with_options(
            "default",
            "llm-ks2o91he406b87js",
            apply_file_upload_lease_request,
            headers,
            runtime,
        )
        return resp
    except Exception as error:
        print(error.message)
        print(error.data.get("Recommend"))
        UtilClient.assert_as_string(error.message)


def upload_file(pre_signed_url, x_bailian_extra, content_type, file_path):
    try:
        # 设置请求头
        headers = {
            "X-bailian-extra": x_bailian_extra,
            "Content-Type": content_type,
        }

        # 读取文档并上传
        with open(file_path, "rb") as file:
            # 下方设置请求方法用于文档上传，需与您在上一步中调用ApplyFileUploadLease接口实际返回的Data.Param中Method字段的值一致
            response = requests.put(pre_signed_url, data=file, headers=headers)

        # 检查响应状态码
        if response.status_code == 200:
            print("File uploaded successfully.")
        else:
            print(f"Failed to upload the file. ResponseCode: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
