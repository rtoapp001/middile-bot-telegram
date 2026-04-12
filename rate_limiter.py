import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple
from database import db

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting to prevent user abuse"""
    
    # Configuration
    MAX_REQUESTS_PER_HOUR = 10  # Maximum requests per hour
    MAX_REQUESTS_PER_DAY = 50   # Maximum requests per day
    COOLDOWN_SECONDS = 60       # Minimum seconds between requests
    
    def __init__(self):
        self.user_request_times: Dict[int, list] = {}
    
    def check_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limits
        Returns: (allowed: bool, message: str)
        """
        try:
            now = datetime.now()
            
            # Initialize user list if not exists
            if user_id not in self.user_request_times:
                self.user_request_times[user_id] = []
            
            # Remove old entries (older than 1 day)
            one_day_ago = now - timedelta(days=1)
            self.user_request_times[user_id] = [
                t for t in self.user_request_times[user_id] 
                if t > one_day_ago
            ]
            
            # Check cooldown
            if self.user_request_times[user_id]:
                last_request = self.user_request_times[user_id][-1]
                cooldown_end = last_request + timedelta(seconds=self.COOLDOWN_SECONDS)
                
                if now < cooldown_end:
                    wait_seconds = int((cooldown_end - now).total_seconds())
                    return False, f"⏳ कृपया {wait_seconds} सेकंड रुकें\n\n(Please wait {wait_seconds} seconds)"
            
            # Check requests per hour
            one_hour_ago = now - timedelta(hours=1)
            requests_this_hour = [t for t in self.user_request_times[user_id] if t > one_hour_ago]
            
            if len(requests_this_hour) >= self.MAX_REQUESTS_PER_HOUR:
                return False, f"❌ घंटे में {self.MAX_REQUESTS_PER_HOUR} से ज्यादा नहीं\n\n(Max {self.MAX_REQUESTS_PER_HOUR} per hour)"
            
            # Check requests per day
            requests_this_day = [t for t in self.user_request_times[user_id] if t > one_day_ago]
            
            if len(requests_this_day) >= self.MAX_REQUESTS_PER_DAY:
                return False, f"❌ दिन में {self.MAX_REQUESTS_PER_DAY} से ज्यादा नहीं\n\n(Max {self.MAX_REQUESTS_PER_DAY} per day)"
            
            # All checks passed
            self.user_request_times[user_id].append(now)
            logger.info(f"✅ Rate limit OK for user {user_id}")
            return True, ""
            
        except Exception as e:
            logger.error(f"❌ Rate limiter error: {e}")
            return True, ""  # Allow on error
    
    def get_user_limits(self, user_id: int) -> Dict:
        """Get remaining requests for user"""
        try:
            now = datetime.now()
            
            if user_id not in self.user_request_times:
                return {
                    'hour': self.MAX_REQUESTS_PER_HOUR,
                    'day': self.MAX_REQUESTS_PER_DAY
                }
            
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(days=1)
            
            requests_this_hour = len([t for t in self.user_request_times[user_id] if t > one_hour_ago])
            requests_this_day = len([t for t in self.user_request_times[user_id] if t > one_day_ago])
            
            return {
                'hour': max(0, self.MAX_REQUESTS_PER_HOUR - requests_this_hour),
                'day': max(0, self.MAX_REQUESTS_PER_DAY - requests_this_day)
            }
        except Exception as e:
            logger.error(f"❌ Error getting limits: {e}")
            return {'hour': self.MAX_REQUESTS_PER_HOUR, 'day': self.MAX_REQUESTS_PER_DAY}


# Initialize rate limiter
rate_limiter = RateLimiter()
