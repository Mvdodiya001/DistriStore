"""
DistriStore — Garbage Collector (Phase 14)
LRU storage eviction to enforce storage quotas.
"""

import asyncio
from backend.utils.logger import get_logger
from backend.utils.config import get_config

logger = get_logger("garbage_collector")

async def storage_monitor_loop(local_store):
    """
    Background loop that checks storage usage every 60 seconds.
    If storage exceeds max_storage_mb, evicts oldest chunks.
    """
    config = get_config()
    
    logger.info(f"Storage Monitor started (Quota: {config.storage.max_storage_mb} MB)")
    
    while True:
        try:
            await asyncio.sleep(60)
            
            max_bytes = config.storage.max_storage_mb * 1024 * 1024
            used_bytes = local_store.get_total_storage_size()
            
            if used_bytes > max_bytes:
                # Evict down to 90% of max capacity to prevent thrashing
                target_bytes = int(used_bytes - (max_bytes * 0.90))
                logger.warning(
                    f"Storage quota exceeded! Used: {used_bytes/1024/1024:.2f}MB, "
                    f"Max: {config.storage.max_storage_mb}MB. Evicting {target_bytes/1024/1024:.2f}MB..."
                )
                
                # Offload eviction to a thread to avoid blocking event loop
                freed = await asyncio.to_thread(local_store.evict_oldest_chunks, target_bytes)
                logger.info(f"Eviction complete. Freed {freed/1024/1024:.2f}MB.")
                
        except asyncio.CancelledError:
            logger.info("Storage Monitor stopped")
            break
        except Exception as e:
            logger.error(f"Storage Monitor error: {e}")
