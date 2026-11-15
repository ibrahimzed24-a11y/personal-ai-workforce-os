import os
import sys
import time
import json
import signal
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional, Set
from pathlib import Path

from core.adapters.supabase_adapter import SupabaseAdapter
from core.orchestrator import Orchestrator
from core.models import TaskCreate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_workforce_os.hybrid_worker")

class HybridRuntimeWorker:
    """
    Local Sovereign Runtime Worker for MacBook Pro.
    Connects to Supabase outbound-only to poll, lease, and execute
    hybrid tasks locally with zero public inbound ports.
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        poll_interval: Optional[float] = None,
        lease_duration: int = 300,
        adapter: Optional[SupabaseAdapter] = None
    ):
        self.node_id = node_id or os.environ.get("HYBRID_NODE_ID", "macbook-pro-primary")
        self.poll_interval = float(poll_interval or os.environ.get("HYBRID_POLL_INTERVAL_SECONDS", "5.0"))
        self.lease_duration = lease_duration
        self.adapter = adapter or SupabaseAdapter()
        self.orchestrator = Orchestrator()
        
        self.is_running = False
        self.current_task: Optional[Dict[str, Any]] = None
        self._processed_idempotency_keys: Set[str] = set()
        self._backoff = self.poll_interval
        self._max_backoff = 60.0

    def get_telemetry(self) -> Dict[str, Any]:
        """Collect local node system metrics and capabilities."""
        return {
            "node_id": self.node_id,
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "capabilities": [
                "browser_automation",
                "local_shell",
                "credentials_vault",
                "python_runtime",
                "three_file_agent_context"
            ],
            "uptime_seconds": time.monotonic(),
            "timestamp": time.time()
        }

    async def register_node(self) -> bool:
        """Register or heartbeat node on Supabase."""
        telemetry = self.get_telemetry()
        res = await self.adapter.heartbeat_node(
            node_id=self.node_id,
            status="online",
            metadata=telemetry
        )
        if res.get("success"):
            logger.info(f"Successfully registered node '{self.node_id}' with Supabase.")
            return True
        elif res.get("offline"):
            logger.warning(f"Supabase is unreachable (offline mode active). Will poll locally.")
            return False
        else:
            logger.warning(f"Failed to register node: {res.get('error')}")
            return False

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a claimed hybrid task locally on the MacBook.
        """
        task_id = str(task["id"])
        idempotency_key = task.get("idempotency_key", task_id)
        title = task.get("title", "Untitled Hybrid Task")
        target_agent = task.get("assigned_agent_id", "core-orchestrator")
        input_payload = task.get("input_payload") or {}

        # 1. Idempotency Check
        if idempotency_key in self._processed_idempotency_keys:
            logger.info(f"Task '{idempotency_key}' already processed locally. Skipping duplicate.")
            return {"status": "completed", "note": "idempotent_replay"}

        logger.info(f"Executing hybrid task '{title}' [{task_id}] via agent '{target_agent}'...")
        self.current_task = task

        try:
            # 2. Dispatch to Local Orchestrator
            local_task_in = TaskCreate(
                title=f"[Cloud] {title}",
                description=task.get("description") or "",
                priority="HIGH",
                context=input_payload,
                target_agent=target_agent
            )
            created = await self.orchestrator.create_task(local_task_in)
            local_id = created.get("id") if isinstance(created, dict) else created.id
            run_result = await self.orchestrator.run_task(local_id)

            output_result = {
                "local_task_id": local_id,
                "status": run_result.get("status", "SUCCESS"),
                "result": run_result,
                "node_id": self.node_id,
                "completed_at": time.time()
            }

            # 3. Report completion to Supabase
            complete_res = await self.adapter.complete_hybrid_task(
                task_id=task_id,
                node_id=self.node_id,
                result=output_result
            )
            if complete_res.get("success"):
                logger.info(f"Task '{task_id}' successfully marked completed in Supabase.")
            else:
                logger.warning(f"Failed to sync completion for task '{task_id}': {complete_res.get('error')}")

            self._processed_idempotency_keys.add(idempotency_key)
            return output_result

        except Exception as e:
            logger.error(f"Error executing hybrid task '{task_id}': {e}", exc_info=True)
            await self.adapter.fail_hybrid_task(
                task_id=task_id,
                node_id=self.node_id,
                error_message=str(e),
                retry=True
            )
            raise e
        finally:
            self.current_task = None

    async def poll_cycle(self) -> Optional[Dict[str, Any]]:
        """
        Execute a single polling and execution cycle.
        """
        if not self.adapter.is_configured():
            logger.debug("Supabase adapter not configured. Running in local-only offline mode.")
            return None

        # 1. Send heartbeat
        telemetry = self.get_telemetry()
        status = "busy" if self.current_task else "online"
        hb_res = await self.adapter.heartbeat_node(self.node_id, status=status, metadata=telemetry)
        
        if hb_res.get("offline"):
            # Supabase is offline; apply exponential backoff
            self._backoff = min(self._backoff * 1.5, self._max_backoff)
            logger.debug(f"Cloud offline, backing off for {self._backoff:.1f}s...")
            return None
        else:
            self._backoff = self.poll_interval

        # 2. Claim next task if idle
        if not self.current_task:
            claim_res = await self.adapter.claim_hybrid_task(self.node_id, lease_seconds=self.lease_duration)
            if claim_res.get("success") and claim_res.get("task"):
                claimed_task = claim_res["task"]
                logger.info(f"Claimed task from Supabase: {claimed_task.get('id')} - {claimed_task.get('title')}")
                return await self.process_task(claimed_task)

        return None

    async def start(self):
        """Start the long-running worker polling loop."""
        self.is_running = True
        logger.info(f"Starting Hybrid Runtime Worker (Node ID: {self.node_id}, Interval: {self.poll_interval}s)...")
        await self.register_node()

        try:
            while self.is_running:
                try:
                    await self.poll_cycle()
                except Exception as e:
                    logger.error(f"Unexpected error in poll cycle: {e}", exc_info=True)
                await asyncio.sleep(self._backoff)
        except asyncio.CancelledError:
            logger.info("Hybrid Worker received stop cancellation.")
        finally:
            await self.stop()

    async def stop(self):
        """Gracefully stop worker and unregister node."""
        self.is_running = False
        logger.info("Stopping Hybrid Runtime Worker...")
        if self.adapter.is_configured():
            await self.adapter.heartbeat_node(self.node_id, status="offline")
        logger.info("Hybrid Runtime Worker stopped.")

def main():
    parser = argparse.ArgumentParser(description="AI Workforce OS - Hybrid Runtime Worker")
    parser.add_argument("--node-id", type=str, default=None, help="Custom node identifier")
    parser.add_argument("--interval", type=float, default=None, help="Poll interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run a single poll cycle and exit")
    args = parser.parse_args()

    worker = HybridRuntimeWorker(node_id=args.node_id, poll_interval=args.interval)

    if args.once:
        logger.info("Running single poll cycle (--once)...")
        res = asyncio.run(worker.poll_cycle())
        logger.info(f"Poll cycle complete. Result: {res}")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def handle_signal():
        logger.info("Termination signal received. Exiting...")
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass

    try:
        loop.run_until_complete(worker.start())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
