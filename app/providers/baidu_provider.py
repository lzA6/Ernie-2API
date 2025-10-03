# app/providers/baidu_provider.py

import httpx
import json
import uuid
import time
import traceback
from typing import Dict, Any, AsyncGenerator, Union, List

from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.providers.base import BaseProvider
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BaiduProvider(BaseProvider):
    """
    百度文心一言提供商
    - 实现了对 ernie.baidu.com 网页版聊天接口的逆向工程。
    - 采用与 Qwen-2api 相同的健壮流式解析器，将百度的SSE流转换为标准OpenAI增量流。
    """

    MODEL_MAP = {
        "ernie-4.5-turbo": "EB45T",
        "ernie-x1": "X1_1",
    }

    # --------------------------------------------------------------------------
    # 核心入口
    # --------------------------------------------------------------------------
    async def chat_completion(self, request_data: Dict[str, Any], original_request: Request) -> Union[StreamingResponse, JSONResponse]:
        try:
            # 目前只支持一个账号，未来可扩展
            account_id = 1
            logger.info(f"检测到文心一言聊天任务，将使用账号 {account_id}...")
            return await self._handle_stream_task(request_data, account_id)
        except Exception as e:
            logger.error(f"处理任务时出错: {type(e).__name__}: {e}")
            traceback.print_exc()
            return JSONResponse(content={"error": {"message": f"处理任务时出错: {e}", "type": "provider_error"}}, status_code=500)

    # --------------------------------------------------------------------------
    # 流式任务处理
    # --------------------------------------------------------------------------
    async def _handle_stream_task(self, request_data: Dict[str, Any], account_id: int) -> StreamingResponse:
        headers = self._prepare_headers(account_id)
        payload = self._prepare_payload(request_data, account_id)
        model_name_for_client = request_data.get("model", "ernie-4.5-turbo")
        url = "https://ernie.baidu.com/eb/chat/conversation/v2"
        
        logger.info(f"   [Baidu-Account-{account_id}] 正在向模型 '{model_name_for_client}' 发送流式请求...")
        return StreamingResponse(self._stream_generator(url, headers, payload, model_name_for_client), media_type="text/event-stream")

    # --------------------------------------------------------------------------
    # 流式解析器
    # --------------------------------------------------------------------------
    async def _stream_generator(self, url: str, headers: Dict, payload: Dict, model_name: str) -> AsyncGenerator[str, None]:
        chat_id = f"chatcmpl-{uuid.uuid4().hex}"
        is_first_chunk = True

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.startswith('data:'):
                            continue
                        
                        raw_data_str = line.strip()[len('data:'):]
                        if not raw_data_str:
                            continue
                        
                        try:
                            baidu_data = json.loads(raw_data_str)
                            
                            # 从 data 字段中提取增量内容
                            delta_content = baidu_data.get("data", {}).get("content")
                            is_end = baidu_data.get("data", {}).get("is_end") == 1

                            if delta_content is None:
                                continue

                            # 首次发送角色信息
                            if is_first_chunk and delta_content:
                                role_chunk = {
                                    "id": chat_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                                    "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
                                }
                                yield f"data: {json.dumps(role_chunk, ensure_ascii=False)}\n\n"
                                is_first_chunk = False

                            # 发送增量内容
                            if delta_content:
                                openai_chunk = {
                                    "id": chat_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                                    "choices": [{"index": 0, "delta": {"content": delta_content}, "finish_reason": None}]
                                }
                                yield f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                            
                            # 如果是最后一个块，发送终止信息
                            if is_end:
                                final_chunk = {
                                    "id": chat_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                                }
                                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                                break # 结束循环
                                
                        except json.JSONDecodeError:
                            logger.warning(f"   [Warning] JSON 解析失败: {raw_data_str}")
                            continue
        
        except Exception as e:
            logger.error(f"   [Error] 流式生成器发生错误: {e}")
            traceback.print_exc()
        
        finally:
            logger.info("   [Stream] 流式传输结束。")
            yield "data: [DONE]\n\n"

    # --------------------------------------------------------------------------
    # 辅助函数
    # --------------------------------------------------------------------------
    def _prepare_headers(self, account_id: int) -> Dict[str, str]:
        try:
            cookie = getattr(settings, f"BAIDU_ACCOUNT_{account_id}_COOKIE")
            acs_token = getattr(settings, f"BAIDU_ACCOUNT_{account_id}_ACS_TOKEN")
        except AttributeError: raise ValueError(f"百度账号 {account_id} 的配置不完整。")
        
        if not cookie or not acs_token: raise ValueError(f"百度账号 {account_id} 的认证信息为空。")
        
        return {
            'accept': 'text/event-stream,application/json, text/event-stream',
            'acs-token': acs_token,
            'connection': 'keep-alive',
            'content-type': 'application/json',
            'cookie': cookie,
            'device-type': 'pc',
            'origin': 'https://ernie.baidu.com',
            'referer': 'https://ernie.baidu.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }

    def _prepare_payload(self, request_data: Dict[str, Any], account_id: int) -> Dict[str, Any]:
        try:
            sign = getattr(settings, f"BAIDU_ACCOUNT_{account_id}_SIGN")
        except AttributeError: raise ValueError(f"百度账号 {account_id} 的 sign 未配置。")
        if not sign: raise ValueError(f"百度账号 {account_id} 的 sign 为空。")

        user_message = request_data.get("messages", [{}])[-1].get("content", "你好")
        model_alias = request_data.get("model", "ernie-4.5-turbo")
        backend_model = self.MODEL_MAP.get(model_alias, "EB45T")

        return {
            "sign": sign,
            "timestamp": int(time.time() * 1000),
            "deviceType": "pc",
            "text": user_message,
            "model": backend_model,
            "sessionId": "",
            "sessionName": "",
            "parentChatId": "0",
            "isNewYiyan": True,
            # ... 其他字段可根据需要添加
        }