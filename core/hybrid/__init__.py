"""
Hybrid Runtime Module for AI Workforce OS.
Coordinates task execution between Vercel serverless cloud endpoints
and sovereign local MacBook execution runtimes.
"""

from core.hybrid.runtime_worker import HybridRuntimeWorker

__all__ = ["HybridRuntimeWorker"]
