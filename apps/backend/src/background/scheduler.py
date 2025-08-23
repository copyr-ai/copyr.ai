import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import List

from ..database.cache_manager import CacheManager
# from ..countries.us.api_clients.hathitrust import HathiTrustClient  # Removed
from ..countries.us.api_clients.library_of_congress import LibraryOfCongressClient
from ..countries.us.api_clients.musicbrainz import MusicBrainzClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.cache_manager = CacheManager()
        self.api_clients = {
            # 'hathitrust': HathiTrustClient(),  # Removed
            'library_of_congress': LibraryOfCongressClient(),
            'musicbrainz': MusicBrainzClient()
        }
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        # Refresh expired cache every 6 hours
        self.scheduler.add_job(
            self.refresh_expired_cache,
            CronTrigger(hour="0,6,12,18"),
            id="refresh_expired_cache",
            name="Refresh expired cache entries"
        )
        
        # Clean up very old cache entries daily at 2 AM
        self.scheduler.add_job(
            self.cleanup_old_cache,
            CronTrigger(hour=2, minute=0),
            id="cleanup_old_cache",
            name="Clean up old cache entries"
        )
        
        # Pre-populate popular searches daily at 3 AM
        self.scheduler.add_job(
            self.prepopulate_popular_searches,
            CronTrigger(hour=3, minute=0),
            id="prepopulate_searches",
            name="Pre-populate popular searches"
        )
    
    async def refresh_expired_cache(self):
        """Refresh works that have expired cache"""
        logger.info("Starting expired cache refresh")
        
        try:
            expired_works = await self.cache_manager.get_expired_works(limit=50)
            logger.info(f"Found {len(expired_works)} expired works to refresh")
            
            for work_data in expired_works:
                try:
                    source_api = work_data['source_api']
                    source_id = work_data['source_id']
                    
                    if source_api in self.api_clients:
                        client = self.api_clients[source_api]
                        
                        # Fetch fresh data from API
                        if hasattr(client, 'get_work_by_id'):
                            fresh_data = await client.get_work_by_id(source_id)
                            if fresh_data:
                                await self.cache_manager.cache_work(
                                    fresh_data, source_api, source_id
                                )
                                logger.info(f"Refreshed cache for {source_api}:{source_id}")
                        
                        # Add delay to respect rate limits
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error refreshing work {work_data.get('id')}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in refresh_expired_cache: {e}")
    
    async def cleanup_old_cache(self):
        """Clean up very old cache entries"""
        logger.info("Starting cache cleanup")
        
        try:
            deleted_count = await self.cache_manager.cleanup_expired_cache(days_old=30)
            logger.info(f"Cleaned up {deleted_count} old cache entries")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_cache: {e}")
    
    async def prepopulate_popular_searches(self):
        """Pre-populate cache with popular/common searches"""
        logger.info("Starting popular searches pre-population")
        
        # Define popular search terms to pre-populate
        popular_searches = [
            ("Shakespeare", "book"),
            ("Mozart", "music"),
            ("Beethoven", "music"),
            ("Mark Twain", "book"),
            ("Charles Dickens", "book"),
            ("Bach", "music"),
            ("Jane Austen", "book"),
            ("Chopin", "music"),
        ]
        
        try:
            for query, work_type in popular_searches:
                try:
                    # Check if we already have recent cache for this search
                    cached_results = await self.cache_manager.get_cached_search(query, work_type)
                    
                    if cached_results is None:  # No cache or expired
                        logger.info(f"Pre-populating search: {query} ({work_type})")
                        
                        # Perform the search using appropriate API clients
                        results = []
                        
                        for client_name, client in self.api_clients.items():
                            if hasattr(client, 'search'):
                                try:
                                    api_results = await client.search(query, work_type=work_type, limit=5)
                                    if api_results:
                                        results.extend(api_results)
                                except Exception as e:
                                    logger.error(f"Error searching {client_name} for {query}: {e}")
                                
                                # Rate limiting
                                await asyncio.sleep(2)
                        
                        # Cache the results
                        if results:
                            await self.cache_manager.cache_search_results(query, work_type, results)
                            logger.info(f"Pre-populated {len(results)} results for '{query}'")
                    
                    # Delay between searches to respect rate limits
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error pre-populating search '{query}': {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in prepopulate_popular_searches: {e}")
    
    async def manual_refresh_work(self, source_api: str, source_id: str):
        """Manually refresh a specific work's cache"""
        try:
            if source_api in self.api_clients:
                client = self.api_clients[source_api]
                
                if hasattr(client, 'get_work_by_id'):
                    fresh_data = await client.get_work_by_id(source_id)
                    if fresh_data:
                        success = await self.cache_manager.cache_work(
                            fresh_data, source_api, source_id
                        )
                        if success:
                            logger.info(f"Manually refreshed cache for {source_api}:{source_id}")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error manually refreshing work {source_api}:{source_id}: {e}")
            return False
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Background scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Background scheduler stopped")

# Global scheduler instance
background_scheduler = BackgroundScheduler()