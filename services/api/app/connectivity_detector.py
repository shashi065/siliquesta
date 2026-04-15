"""
Connectivity Detector - Online/Offline Status Management
========================================================

Automatically detects network connectivity and switches between
edge (offline) and cloud (online) AI models.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ConnectivityStatus:
    """Current connectivity status"""
    is_online: bool
    last_check: datetime = field(default_factory=datetime.now)
    last_successful_connection: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    latency_ms: Optional[float] = None
    primary_service: str = "cloud"  # "cloud" or "edge"
    fallback_active: bool = False
    check_history: Dict[str, Any] = field(default_factory=dict)


class ConnectivityDetector:
    """
    Detects network connectivity and automatically switches between
    edge (offline/local) and cloud (online) AI services.
    
    Features:
    - Periodic connectivity checks
    - Latency measurement
    - Failover to edge on network loss
    - Automatic recovery to cloud
    - Health monitoring
    """
    
    def __init__(self, 
                 check_interval_seconds: int = 30,
                 failure_threshold: int = 3,
                 success_threshold: int = 2):
        """
        Initialize connectivity detector.
        
        Args:
            check_interval_seconds: How often to check connectivity
            failure_threshold: Failures before switching to edge
            success_threshold: Successes before switching back to cloud
        """
        self.status = ConnectivityStatus()
        self.check_interval = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        
        # Cloud endpoints to check
        self.health_endpoints = [
            "http://localhost:8000/api/v1/health",  # Local API
            "http://api.siliquesta.com/health",     # Cloud API (placeholder)
        ]
        
        self.checker_task: Optional[asyncio.Task] = None
        
        logger.info(f"✓ ConnectivityDetector initialized (interval: {check_interval_seconds}s)")
    
    async def start_monitoring(self):
        """Start background connectivity monitoring"""
        if self.checker_task is not None:
            return
        
        self.checker_task = asyncio.create_task(self._monitoring_loop())
        logger.info("✓ Connectivity monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self.checker_task:
            self.checker_task.cancel()
            try:
                await self.checker_task
            except asyncio.CancelledError:
                pass
            self.checker_task = None
            logger.info("✓ Connectivity monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self.check_connectivity()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
    
    async def check_connectivity(self) -> bool:
        """
        Check if cloud services are reachable.
        
        Returns:
            True if online, False if offline
        """
        try:
            # Try to reach health endpoint
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = datetime.now()
                
                # Try primary endpoint first
                for endpoint in self.health_endpoints:
                    try:
                        async with session.get(endpoint) as resp:
                            if resp.status == 200:
                                latency = (datetime.now() - start_time).total_seconds() * 1000
                                
                                self.status.is_online = True
                                self.status.latency_ms = latency
                                self.status.last_check = datetime.now()
                                self.status.last_successful_connection = datetime.now()
                                self.status.consecutive_successes += 1
                                self.status.consecutive_failures = 0
                                
                                # Switch back to cloud if threshold met
                                if self.status.consecutive_successes >= self.success_threshold:
                                    self.status.primary_service = "cloud"
                                    if self.status.fallback_active:
                                        logger.info(f"✅ Cloud service recovered, switching to cloud (latency: {latency:.1f}ms)")
                                        self.status.fallback_active = False
                                
                                logger.debug(f"✓ Cloud connectivity OK ({latency:.1f}ms)")
                                return True
                    except Exception as e:
                        logger.debug(f"Health check failed for {endpoint}: {e}")
                        continue
                
                # All endpoints failed
                raise Exception("All health endpoints unreachable")
                
        except Exception as e:
            logger.debug(f"Connectivity check failed: {e}")
            
            self.status.is_online = False
            self.status.consecutive_failures += 1
            self.status.consecutive_successes = 0
            self.status.last_check = datetime.now()
            
            # Switch to edge after threshold failures
            if self.status.consecutive_failures >= self.failure_threshold:
                self.status.primary_service = "edge"
                if not self.status.fallback_active:
                    logger.warning(f"❌ Cloud unreachable ({self.status.consecutive_failures} failures), switching to edge mode (ONNX)")
                    self.status.fallback_active = True
            
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current connectivity status"""
        return {
            "is_online": self.status.is_online,
            "primary_service": self.status.primary_service,
            "fallback_active": self.status.fallback_active,
            "latency_ms": self.status.latency_ms,
            "consecutive_failures": self.status.consecutive_failures,
            "consecutive_successes": self.status.consecutive_successes,
            "last_check": self.status.last_check.isoformat(),
            "last_successful_connection": self.status.last_successful_connection.isoformat() if self.status.last_successful_connection else None
        }
    
    def is_online(self) -> bool:
        """Check if currently online"""
        return self.status.is_online
    
    def use_edge(self) -> bool:
        """Should use edge (ONNX) models?"""
        return self.status.primary_service == "edge"
    
    def use_cloud(self) -> bool:
        """Should use cloud AI backend?"""
        return self.status.primary_service == "cloud"
    
    def get_recommended_model_source(self) -> str:
        """Get recommended model source"""
        return "edge" if self.use_edge() else "cloud"


# Global detector instance
_connectivity_detector: Optional[ConnectivityDetector] = None


def get_connectivity_detector() -> ConnectivityDetector:
    """Get or create global connectivity detector"""
    global _connectivity_detector
    if _connectivity_detector is None:
        _connectivity_detector = ConnectivityDetector(
            check_interval_seconds=30,
            failure_threshold=3,
            success_threshold=2
        )
    return _connectivity_detector


async def initialize_connectivity_detector():
    """Initialize and start connectivity monitoring"""
    detector = get_connectivity_detector()
    await detector.start_monitoring()
    logger.info("✓ Connectivity detector initialized and monitoring started")


async def shutdown_connectivity_detector():
    """Shutdown connectivity monitoring"""
    detector = get_connectivity_detector()
    await detector.stop_monitoring()
    logger.info("✓ Connectivity detector shutdown")
