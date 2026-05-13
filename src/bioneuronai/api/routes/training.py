# -*- coding: utf-8 -*-
"""Training job and model promotion routes."""

from typing import Any

from fastapi import APIRouter

from bioneuronai.api.models import ApiResponse, ModelPromoteRequest, TrainingStartRequest


def create_router(training_job_manager: Any, model_promotion_manager: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/training/start", response_model=ApiResponse, tags=["training"])
    async def start_training(req: TrainingStartRequest):
        """登記遠端訓練作業，或明確啟動本機 unified_trainer subprocess。"""
        try:
            data = training_job_manager.start(req)
            mode_label = "遠端訓練已登記" if req.execution_mode == "external" else "本機訓練已啟動"
            return ApiResponse(success=True, message=mode_label, data=data)
        except Exception as exc:
            return ApiResponse(success=False, message=f"訓練作業啟動失敗: {exc}")

    @router.get("/api/v1/training", response_model=ApiResponse, tags=["training"])
    async def list_training_jobs():
        """列出目前 API 進程追蹤中的訓練作業。"""
        return ApiResponse(
            success=True,
            message="訓練作業列表讀取完成",
            data={"jobs": training_job_manager.list_jobs()},
        )

    @router.get("/api/v1/training/{job_id}", response_model=ApiResponse, tags=["training"])
    async def get_training_job(job_id: str):
        """查詢訓練作業狀態。"""
        data = training_job_manager.get(job_id)
        success = data.get("status") != "not_found"
        return ApiResponse(
            success=success,
            message="訓練作業狀態讀取完成" if success else "找不到訓練作業",
            data=data,
        )

    @router.get("/api/v1/model/status", response_model=ApiResponse, tags=["model"])
    async def get_model_status():
        """讀取目前 runtime 模型設定與交易引擎載入狀態。"""
        return ApiResponse(success=True, message="模型狀態讀取完成", data=model_promotion_manager.status())

    @router.post("/api/v1/model/promote", response_model=ApiResponse, tags=["model"])
    async def promote_model(req: ModelPromoteRequest):
        """將訓練完成的模型登記為後續 runtime 使用來源。"""
        try:
            data = model_promotion_manager.promote(req)
            return ApiResponse(success=True, message="模型 promote 完成", data=data)
        except Exception as exc:
            return ApiResponse(success=False, message=f"模型 promote 失敗: {exc}")

    return router
