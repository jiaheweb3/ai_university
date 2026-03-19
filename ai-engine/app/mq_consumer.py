"""
AetherVerse AI Engine — RabbitMQ 消费者
监听 evaluate / generate 请求队列，处理后发布到响应队列
"""

from __future__ import annotations

import asyncio
import json

import redis.asyncio as aioredis
import structlog
from aio_pika import ExchangeType, IncomingMessage, Message
from aio_pika.abc import AbstractRobustConnection

from shared.schemas import AgentContext, RoomContext

from .config import Settings
from .creation.image_generator import start_image_generation
from .memory.summarizer import summarize_memories
from .model_router import ModelRouter
from .moderation.moderator import check_text
from .orchestrator.evaluator import evaluate_should_reply
from .orchestrator.generator import generate_reply
from .schemas import (
    EvaluateRequest,
    GenerateRequest,
    ImageGenAccepted,
    MemorySummarizeResponse,
    ModerationResult,
)

logger = structlog.get_logger(__name__)

# 队列名称常量
Q_EVALUATE_REQ = "ai.chat.evaluate.request"
Q_EVALUATE_RESP = "ai.chat.evaluate.response"
Q_GENERATE_REQ = "ai.chat.generate.request"
Q_GENERATE_RESP = "ai.chat.generate.response"
Q_MEMORY_REQ = "ai.memory.summarize.request"
Q_MEMORY_RESP = "ai.memory.summarize.result"
Q_CREATION_REQ = "ai.creation.request"
Q_CREATION_RESP = "ai.creation.result"
Q_MODERATION_REQ = "ai.moderation.request"
Q_MODERATION_RESP = "ai.moderation.result"


class MQConsumer:
    """RabbitMQ 异步消费者"""

    def __init__(
        self,
        conn: AbstractRobustConnection,
        settings: Settings,
        model_router: ModelRouter,
        redis: aioredis.Redis,
    ) -> None:
        self._conn = conn
        self._settings = settings
        self._model_router = model_router
        self._redis = redis
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """启动所有消费者"""
        channel = await self._conn.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            self._settings.MQ_EXCHANGE,
            ExchangeType.TOPIC,
            durable=True,
        )

        # 声明 + 绑定队列
        eval_queue = await channel.declare_queue(Q_EVALUATE_REQ, durable=True)
        await eval_queue.bind(exchange, routing_key=Q_EVALUATE_REQ)

        gen_queue = await channel.declare_queue(Q_GENERATE_REQ, durable=True)
        await gen_queue.bind(exchange, routing_key=Q_GENERATE_REQ)

        mem_queue = await channel.declare_queue(Q_MEMORY_REQ, durable=True)
        await mem_queue.bind(exchange, routing_key=Q_MEMORY_REQ)

        creation_queue = await channel.declare_queue(Q_CREATION_REQ, durable=True)
        await creation_queue.bind(exchange, routing_key=Q_CREATION_REQ)

        mod_queue = await channel.declare_queue(Q_MODERATION_REQ, durable=True)
        await mod_queue.bind(exchange, routing_key=Q_MODERATION_REQ)

        # 响应队列（用于发布）
        for q in [Q_EVALUATE_RESP, Q_GENERATE_RESP, Q_MEMORY_RESP, Q_CREATION_RESP, Q_MODERATION_RESP]:
            await channel.declare_queue(q, durable=True)

        # 启动消费
        self._tasks.append(asyncio.create_task(self._consume(eval_queue, self._handle_evaluate, exchange)))
        self._tasks.append(asyncio.create_task(self._consume(gen_queue, self._handle_generate, exchange)))
        self._tasks.append(asyncio.create_task(self._consume(mem_queue, self._handle_memory, exchange)))
        self._tasks.append(asyncio.create_task(self._consume(creation_queue, self._handle_creation, exchange)))
        self._tasks.append(asyncio.create_task(self._consume(mod_queue, self._handle_moderation, exchange)))

        all_queues = [Q_EVALUATE_REQ, Q_GENERATE_REQ, Q_MEMORY_REQ, Q_CREATION_REQ, Q_MODERATION_REQ]
        await logger.ainfo("mq_consumers_started", queues=all_queues)

    async def stop(self) -> None:
        """停止所有消费者"""
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        await logger.ainfo("mq_consumers_stopped")

    async def _consume(self, queue, handler, exchange) -> None:
        """泛化消费循环"""
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        await handler(message, exchange)
                    except Exception as exc:
                        await logger.aerror(
                            "mq_message_handler_error",
                            queue=queue.name,
                            error=str(exc),
                        )

    async def _handle_evaluate(self, message: IncomingMessage, exchange) -> None:
        """处理监听评估请求"""
        body = json.loads(message.body.decode())
        req = EvaluateRequest(**body)

        result = await evaluate_should_reply(
            agent=req.agent,
            room=req.room,
            trigger_type=req.trigger_type,
            model_router=self._model_router,
        )

        # 发布响应
        resp_body = result.model_dump_json().encode()
        await exchange.publish(
            Message(body=resp_body, correlation_id=message.correlation_id),
            routing_key=Q_EVALUATE_RESP,
        )

    async def _handle_generate(self, message: IncomingMessage, exchange) -> None:
        """处理发言生成请求"""
        body = json.loads(message.body.decode())
        req = GenerateRequest(**body)

        result = await generate_reply(
            agent=req.agent,
            room=req.room,
            request_id=req.request_id,
            model_router=self._model_router,
            redis=self._redis,
            max_tokens=req.max_tokens,
        )

        resp_body = result.model_dump_json().encode()
        await exchange.publish(
            Message(body=resp_body, correlation_id=message.correlation_id),
            routing_key=Q_GENERATE_RESP,
        )

    async def _handle_memory(self, message: IncomingMessage, exchange) -> None:
        """处理记忆摘要请求"""
        body = json.loads(message.body.decode())

        summary, token_count, model = await summarize_memories(
            agent_id=body.get("agent_id", ""),
            persona_config=body.get("persona_config"),
            memories=body.get("memories", []),
            model_router=self._model_router,
            max_tokens=body.get("max_tokens", 500),
        )

        resp = MemorySummarizeResponse(summary=summary, token_count=token_count, model=model)
        await exchange.publish(
            Message(body=resp.model_dump_json().encode(), correlation_id=message.correlation_id),
            routing_key=Q_MEMORY_RESP,
        )

    async def _handle_creation(self, message: IncomingMessage, exchange) -> None:
        """处理图片生成请求"""
        body = json.loads(message.body.decode())

        task_id, estimated = await start_image_generation(
            agent=body.get("agent", {}),
            topic=body.get("topic", {}),
            request_id=body.get("request_id", ""),
            redis=self._redis,
            model_router=self._model_router,
            image_size=body.get("image_size", "1024x1024"),
        )

        resp = ImageGenAccepted(task_id=task_id, estimated_seconds=estimated)
        await exchange.publish(
            Message(body=resp.model_dump_json().encode(), correlation_id=message.correlation_id),
            routing_key=Q_CREATION_RESP,
        )

    async def _handle_moderation(self, message: IncomingMessage, exchange) -> None:
        """处理内容审核请求"""
        body = json.loads(message.body.decode())

        result = await check_text(
            text=body.get("text", ""),
            model_router=self._model_router,
            context=body.get("context"),
            sender_type=body.get("sender_type", "user"),
        )

        resp = ModerationResult(**result)
        await exchange.publish(
            Message(body=resp.model_dump_json().encode(), correlation_id=message.correlation_id),
            routing_key=Q_MODERATION_RESP,
        )
