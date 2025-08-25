import hashlib
import os
from time import sleep
from typing import List, Dict, Any
import dashscope
from alibabacloud_bailian20231229.client import Client as bailian20231229Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_bailian20231229.models import (
    ApplyFileUploadLeaseResponse,
    AddFileResponse,
    DescribeFileResponse,
)
import requests
from urllib.parse import urlparse
import os
from http import HTTPStatus
from dashscope import Application


def analyze_file_with_dashscope(file_path: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")
    dashscope.api_key = api_key
    client = create_client()
    lease: ApplyFileUploadLeaseResponse = create_upload_lease(client, file_path)
    upload_file(
        lease.body.data.param.url,
        lease.body.data.param.headers["X-bailian-extra"],
        lease.body.data.param.headers["Content-Type"],
        file_path,
    )
    file_resp: AddFileResponse = add_files_to_dashscope(
        client, lease.body.data.file_upload_lease_id
    )
    call_dashscope_api(client, file_resp.body.data.file_id)


def get_file_status(client, file_id):
    runtime = util_models.RuntimeOptions()
    headers = {}
    try:
        status: DescribeFileResponse = client.describe_file_with_options(
            "llm-ks2o91he406b87js",
            file_id,
            headers,
            runtime,
        )
        return status.body.data.status
    except Exception as error:
        print(error.message)
        print(error.data.get("Recommend"))
        UtilClient.assert_as_string(error.message)


def call_dashscope_api(client, file_id):
    # 循环等待文件解析完成
    i = 0
    while True:
        if i < 99:
            status = get_file_status(client, file_id)
            if status == "FILE_IS_READY":
                print("文件解析完成")
                break
            elif status in [
                "PARSE_FAILED",
                "SAFE_CHECK_FAILED",
                "INDEX_BUILDING_FAILED",
            ]:
                print("文件解析失败")
                return
            else:
                print(f"文件正在解析中...{status}")
            i = i + 1
            sleep(5)
        else:
            print("文件解析超时")
            return
    # sleep(30)
    response = Application.call(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        app_id=os.getenv("DASHSCOPE_APP_ID"),
        prompt="请按照指令分析文件并输出数据",
        rag_options={
            "session_file_ids": [file_id],
        },
    )
    if response.status_code != HTTPStatus.OK:
        print(f"request_id={response.request_id}")
        print(f"code={response.status_code}")
        print(f"message={response.message}")
    else:
        print("%s\n" % (response.output.text))


def create_client() -> bailian20231229Client:
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


def create_upload_lease(client, file_path: str) -> Dict[str, Any]:
    file_name = os.path.basename(file_path)
    apply_file_upload_lease_request = (
        bailian_20231229_models.ApplyFileUploadLeaseRequest(
            md_5=calculate_md5(file_path),
            file_name=file_name,
            size_in_bytes=os.path.getsize(file_path),
            category_type="SESSION_FILE",
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


def add_files_to_dashscope(client, lease_id):
    add_file_request = bailian_20231229_models.AddFileRequest(
        lease_id=lease_id,
        parser="DASHSCOPE_DOCMIND",
        category_id="default",
        category_type="SESSION_FILE",
    )
    runtime = util_models.RuntimeOptions()
    headers = {}
    try:
        # 复制代码运行请自行打印 API 的返回值
        resp = client.add_file_with_options(
            "llm-ks2o91he406b87js", add_file_request, headers, runtime
        )
        return resp
    except Exception as error:
        # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
        # 错误 message
        print(error.message)
        # 诊断地址
        print(error.data.get("Recommend"))
        UtilClient.assert_as_string(error.message)
