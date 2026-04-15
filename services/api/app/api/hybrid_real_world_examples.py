"""
Hybrid AI - Real-World Integration Examples
============================================

Practical examples of integrating SILIQUESTA Hybrid AI 
in production environments (IoT, mobile, edge devices).

Author: SILIQUESTA Team
Version: 1.0
"""

import asyncio
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

from app.api.hybrid_api_guide import HybridAIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: IoT Sensor Data Processing
# ============================================================================

@dataclass
class SensorReading:
    """IoT sensor reading"""
    device_id: str
    timestamp: datetime
    wn: float          # Normalized frequency (GHz)
    wp: float          # Normalized power (W)
    vdd: float         # Voltage (V)
    temp: float        # Temperature (°C)
    is_online: bool    # Network connectivity


class IoTSensorProcessor:
    """
    Process IoT sensor data with hybrid AI.
    
    Scenario:
    - IoT devices send sensor readings at fixed intervals
    - Device may be online or offline
    - Use cloud AI when online for best accuracy
    - Fall back to edge AI when offline (no data loss)
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.client = HybridAIClient(api_url)
        self.readings_buffer = deque(maxlen=1000)
        self.predictions_buffer = deque(maxlen=1000)
    
    async def process_reading(self, reading: SensorReading) -> Dict[str, Any]:
        """
        Process a single sensor reading.
        
        Returns prediction with model source information.
        """
        
        logger.info(f"Processing reading from {reading.device_id}")
        
        # Store reading
        self.readings_buffer.append(reading)
        
        # Prepare input for model
        inputs = {
            "wn": reading.wn,
            "wp": reading.wp,
            "vdd": reading.vdd,
            "temp": reading.temp
        }
        
        # Make prediction
        try:
            result = self.client.predict(
                model_name="digital_twin",
                inputs=inputs,
                user_preference="auto"  # Let system decide
            )
            
            # Add metadata
            result["device_id"] = reading.device_id
            result["reading_timestamp"] = reading.timestamp.isoformat()
            result["device_was_online"] = reading.is_online
            
            # Store prediction
            self.predictions_buffer.append(result)
            
            # Log appropriately
            source = result['model_source']
            if source == 'edge' and reading.is_online:
                logger.warning(f"Cloud failed, using fallback edge")
            elif source == 'cloud' and not reading.is_online:
                logger.warning(f"Device offline but prediction via cloud")
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for {reading.device_id}: {e}")
            raise
    
    async def process_batch(self, readings: List[SensorReading]) -> List[Dict[str, Any]]:
        """Process multiple sensor readings efficiently"""
        
        logger.info(f"Processing batch of {len(readings)} readings")
        
        # Prepare batch request
        batch_request = [
            {
                "model_name": "digital_twin",
                "inputs": {
                    "wn": r.wn,
                    "wp": r.wp,
                    "vdd": r.vdd,
                    "temp": r.temp
                },
                "user_preference": "auto"
            }
            for r in readings
        ]
        
        # Process batch
        results = self.client.batch_predict(batch_request)
        
        # Add metadata
        for result, reading in zip(results, readings):
            result["device_id"] = reading.device_id
            result["reading_timestamp"] = reading.timestamp.isoformat()
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        
        edge_count = sum(
            1 for p in self.predictions_buffer 
            if p['model_source'] == 'edge'
        )
        cloud_count = len(self.predictions_buffer) - edge_count
        
        return {
            "total_readings": len(self.readings_buffer),
            "total_predictions": len(self.predictions_buffer),
            "edge_predictions": edge_count,
            "cloud_predictions": cloud_count,
            "edge_percentage": f"{100*edge_count/len(self.predictions_buffer):.1f}%"
        }


# ============================================================================
# Example 2: Mobile App Integration
# ============================================================================

class MobileAppAPI:
    """
    Backend API for mobile apps.
    
    Scenario:
    - Mobile app makes predictions while mobile device is online/offline
    - Requests may be sent from cellular or WiFi networks
    - Need responsive feedback regardless of network
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.client = HybridAIClient(api_url)
    
    async def quick_predict(self, inputs: Dict[str, float]) -> Dict[str, Any]:
        """
        Make a prediction for mobile app.
        
        Optimized for:
        - Fast response (use edge if offline)
        - Mobile connectivity variation
        - Minimal data usage
        """
        
        result = self.client.predict(
            model_name="digital_twin",
            inputs=inputs,
            user_preference="auto"
        )
        
        # Format for mobile app
        return {
            "result": result['result'],
            "confidence": result['confidence'],
            "source": "Local" if result['model_source'] == 'edge' else "Cloud",
            "time_ms": result['execution_time_ms'],
            "timestamp": result['timestamp']
        }
    
    async def sync_cached_predictions(self, cached_data: List[Dict]) -> None:
        """
        Sync cached predictions made offline to cloud.
        
        Scenario:
        - Mobile app made predictions while offline using edge models
        - Now back online, send results to cloud for analytics
        """
        
        logger.info(f"Syncing {len(cached_data)} cached predictions")
        
        # Send to server for logging/analytics
        # This would typically be to a database or analytics service
        for prediction in cached_data:
            logger.info(
                f"Synced: {prediction['model']} "
                f"(local exec on device)"
            )


# ============================================================================
# Example 3: Edge Device (Raspberry Pi, Jetson, etc.)
# ============================================================================

class EdgeDeviceProcessor:
    """
    Run on edge devices (Raspberry Pi, Jetson Nano, etc).
    
    Scenario:
    - Edge device with local ONNX models for reliable operation
    - Optional cloud connectivity for advanced analysis
    - Prioritize reliability over maximum accuracy
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.client = HybridAIClient(api_url)
        self.local_cache = deque(maxlen=100)
    
    async def process_with_priority_reliability(
        self,
        inputs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Process with priority on reliability.
        
        Prefer edge (local) execution for guaranteed operation.
        Only use cloud if explicitly requested.
        """
        
        # Force edge model for reliability
        self.client.force_edge()
        
        result = self.client.predict(
            model_name="digital_twin",
            inputs=inputs,
            user_preference="edge"
        )
        
        # Cache result locally
        self.local_cache.append(result)
        
        logger.info(f"Edge processing: {result['execution_time_ms']:.1f}ms")
        
        return result
    
    async def periodic_cloud_sync(self) -> None:
        """
        Periodically sync cached data to cloud when available.
        
        Non-blocking operation that runs in background.
        """
        
        if not self.local_cache:
            return
        
        try:
            # Test if cloud available
            status = self.client.get_connectivity()
            
            if not status['is_online']:
                logger.info("Cloud unavailable, skipping sync")
                return
            
            logger.info(f"Cloud available, syncing {len(self.local_cache)} records")
            
            # Switch to cloud temporarily
            self.client.force_cloud()
            
            # Re-process cached items for cloud backup
            # (would typically send to database instead)
            for cached in list(self.local_cache):
                logger.info(f"Backed up: {cached['result']}")
            
            # Back to edge
            self.client.force_edge()
            
        except Exception as e:
            logger.warning(f"Cloud sync failed: {e}")


# ============================================================================
# Example 4: Real-Time Monitoring Dashboard
# ============================================================================

class RealTimeMonitor:
    """
    Real-time system monitoring for dashboards.
    
    Scenario:
    - Display live system status on web dashboard
    - Track edge vs cloud usage patterns
    - Alert on connectivity issues
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.client = HybridAIClient(api_url)
        self.metrics_history = deque(maxlen=1440)  # 24 hours at 1-min intervals
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        
        status = self.client.get_status()
        connectivity = self.client.get_connectivity()
        performance = self.client.get_performance()
        
        timestamp = datetime.now()
        
        metrics = {
            "timestamp": timestamp.isoformat(),
            "model_source": status['model_source'],
            "is_online": connectivity['is_online'],
            "latency_ms": connectivity.get('latency_ms'),
            "total_requests": status['total_requests_processed'],
            "performance_stats": performance['performance_stats'],
            "consecutive_successes": connectivity['consecutive_successes'],
            "consecutive_failures": connectivity['consecutive_failures']
        }
        
        self.metrics_history.append(metrics)
        
        return metrics
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data formatted for dashboard"""
        
        latest = self.collect_metrics()
        
        # Calculate trends
        if len(self.metrics_history) > 1:
            recent = list(self.metrics_history)[-10:]
            edge_count = sum(1 for m in recent if m['model_source'] == 'edge')
            cloud_count = len(recent) - edge_count
        else:
            edge_count = cloud_count = 0
        
        return {
            "current": latest,
            "trends": {
                "edge_vs_cloud": {"edge": edge_count, "cloud": cloud_count},
                "online_time": f"{latest['consecutive_successes']} checks"
            },
            "alerts": self._check_alerts(latest)
        }
    
    def _check_alerts(self, metrics: Dict) -> List[str]:
        """Check for alert conditions"""
        
        alerts = []
        
        if not metrics['is_online']:
            alerts.append("⚠️  System offline - using edge models")
        
        if metrics['consecutive_failures'] > 5:
            alerts.append("🔴 Cloud connectivity failing")
        
        perf = metrics['performance_stats']
        if perf.get('avg_execution_time_ms', 0) > 500:
            alerts.append("⚠️  High latency detected")
        
        return alerts
    
    async def get_history(self, minutes: int = 60) -> List[Dict]:
        """Get metrics history for time range"""
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        return [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff
        ]


# ============================================================================
# Example 5: Load Balancing Across Multiple Services
# ============================================================================

class HybridAILoadBalancer:
    """
    Load balance predictions across multiple hybrid AI instances.
    
    Scenario:
    - Multiple API instances running hybr
    - Distribute load based on current availability
    - Prefer local (edge) execution when possible
    """
    
    def __init__(self, api_urls: List[str]):
        """
        Initialize with list of API endpoints.
        
        Args:
            api_urls: List of API URLs to balance across
        """
        self.clients = [HybridAIClient(url) for url in api_urls]
        self.request_count = 0
    
    async def predict_load_balanced(
        self,
        model_name: str,
        inputs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Make prediction with load balancing.
        
        Strategy:
        - Check which instances are using edge models
        - Prefer edge (local) execution
        - Fall back to cloud if needed
        """
        
        results = []
        
        # Check each instance
        for client in self.clients:
            try:
                status = client.get_status()
                source = status['model_source']
                
                # Prefer edge instances
                if source == 'edge':
                    logger.info("Using edge instance")
                    result = client.predict(model_name, inputs)
                    result['_instance_type'] = 'edge'
                    return result
                
                results.append((client, source))
                
            except Exception as e:
                logger.warning(f"Instance unavailable: {e}")
                continue
        
        # Fall back to first available instance
        if results:
            client, source = results[0]
            logger.info(f"Using cloud instance")
            result = client.predict(model_name, inputs)
            result['_instance_type'] = 'cloud'
            return result
        
        raise Exception("No instances available")


# ============================================================================
# Example 6: Batch Processing Pipeline
# ============================================================================

class BatchProcessingPipeline:
    """
    Process large batches of predictions efficiently.
    
    Scenario:
    - Process historical data in batches
    - Optimize for throughput and cost
    - Minimize network roundtrips
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.client = HybridAIClient(api_url)
    
    async def process_large_batch(
        self,
        data: List[Dict[str, float]],
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Process large dataset in optimized batches.
        
        Args:
            data: List of input dictionaries
            batch_size: Number of predictions per batch
        
        Returns:
            List of all predictions
        """
        
        all_results = []
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        logger.info(f"Processing {len(data)} items in {total_batches} batches")
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Batch {batch_num}/{total_batches}")
            
            # Prepare batch request
            predictions = [
                {
                    "model_name": "digital_twin",
                    "inputs": item,
                    "user_preference": "auto"
                }
                for item in batch
            ]
            
            # Process batch
            results = self.client.batch_predict(predictions)
            all_results.extend(results)
            
            # Log batch statistics
            edge_count = sum(1 for r in results if r['model_source'] == 'edge')
            logger.info(
                f"  Completed: {edge_count} edge, "
                f"{len(results)-edge_count} cloud"
            )
        
        return all_results
    
    async def process_streaming(self, data_generator):
        """
        Process data stream continuously.
        
        Scenario:
        - Real-time data stream (sensor, IoT, queue)
        - Process as data arrives
        - Apply backpressure if needed
        """
        
        async for item in data_generator:
            try:
                result = self.client.predict(
                    "digital_twin",
                    item
                )
                
                yield result
                
            except Exception as e:
                logger.error(f"Stream processing error: {e}")
                # Continue with next item


# ============================================================================
# Demonstration
# ============================================================================

async def demonstrate_all_examples():
    """Demonstrate all integration examples"""
    
    print("\n" + "="*70)
    print("HYBRID AI - REAL-WORLD INTEGRATION EXAMPLES")
    print("="*70)
    
    # Example 1: IoT Sensor Processing
    print("\n" + "="*70)
    print("1. IoT SENSOR DATA PROCESSING")
    print("="*70)
    
    processor = IoTSensorProcessor()
    
    # Simulate sensor readings
    reading = SensorReading(
        device_id="device_001",
        timestamp=datetime.now(),
        wn=2.5, wp=5.2, vdd=0.9, temp=25,
        is_online=True
    )
    
    result = await processor.process_reading(reading)
    print(f"✓ Processed sensor from {reading.device_id}")
    print(f"  Model source: {result['model_source']}")
    print(f"  Time: {result['execution_time_ms']:.1f}ms")
    
    stats = processor.get_statistics()
    print(f"  Statistics: {stats}")
    
    # Example 2: Real-Time Monitoring
    print("\n" + "="*70)
    print("2. REAL-TIME MONITORING DASHBOARD")
    print("="*70)
    
    monitor = RealTimeMonitor()
    
    metrics = await monitor.collect_metrics()
    print(f"✓ Collected metrics")
    print(f"  Model source: {metrics['model_source']}")
    print(f"  Online: {metrics['is_online']}")
    print(f"  Total requests: {metrics['total_requests']}")
    
    # Example 3: Edge Device
    print("\n" + "="*70)
    print("3. EDGE DEVICE PROCESSING")
    print("="*70)
    
    edge_proc = EdgeDeviceProcessor()
    
    inputs = {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}
    result = await edge_proc.process_with_priority_reliability(inputs)
    print(f"✓ Edge processing completed")
    print(f"  Time: {result['execution_time_ms']:.1f}ms")
    print(f"  Reliability: Using local ONNX models")
    
    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70)


if __name__ == "__main__":
    print("""
SILIQUESTA Hybrid AI - Real-World Integration Examples

This module contains practical examples of integrating the hybrid AI system:

1. IoT Sensor Data Processing
   - Process sensor readings with automatic fallback
   - Handle online/offline scenarios
   
2. Mobile App Integration
   - Backend API for mobile applications
   - Sync cached predictions when back online
   
3. Edge Device Processing
   - Run on edge devices (Raspberry Pi, Jetson)
   - Prioritize reliability over accuracy
   
4. Real-Time Monitoring Dashboard
   - Display system status in real-time
   - Track metrics and performance
   
5. Load Balancing
   - Balance across multiple instances
   - Prefer edge execution
   
6. Batch Processing Pipeline
   - Process large datasets efficiently
   - Stream processing support

To run examples:
    python app/api/hybrid_real_world_examples.py

To use in your project:
    from app.api.hybrid_real_world_examples import IoTSensorProcessor
    processor = IoTSensorProcessor()
    result = await processor.process_reading(sensor_reading)
""")
