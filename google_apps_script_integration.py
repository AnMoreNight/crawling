"""
Google Apps Script Integration Module
Sends crawl results to your deployed Google Apps Script
"""

import requests
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleAppsScriptIntegration:
    """Integrates with deployed Google Apps Script to send crawl results."""
    
    def __init__(self, script_url: str):
        """
        Initialize Google Apps Script integration.
        
        Args:
            script_url: URL of deployed Google Apps Script
                       e.g., https://script.google.com/macros/s/AKfycb.../exec
        """
        self.script_url = script_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CrawlerBot/1.0',
            'Content-Type': 'application/json'
        })
    
    def send_result(self, result: Dict) -> bool:
        """
        Send a single crawl result to Google Apps Script.
        
        Args:
            result: Dictionary with crawl result
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Send as single-item array (the Apps Script expects array format)
            payload = [result]
            
            response = self.session.post(
                self.script_url,
                json=payload,
                timeout=30,
                allow_redirects=True
            )
            
            # Accept 2xx (success) or 3xx (redirect from Apps Script)
            if 200 <= response.status_code < 400:
                try:
                    resp_json = response.json()
                    if resp_json.get('success'):
                        logger.info(f"✓ Sent to Google Sheet: {result.get('url')}")
                        return True
                    else:
                        logger.warning(f"✗ Script error for {result.get('url')}: {resp_json.get('error')}")
                        return False
                except:
                    # If response is not JSON, check if status code indicates success
                    logger.info(f"✓ Sent to Google Sheet: {result.get('url')} (HTTP {response.status_code})")
                    return True
            else:
                logger.warning(f"✗ Failed to send {result.get('url')}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to Google Apps Script: {e}")
            return False
    
    def send_batch(self, results: List[Dict]) -> Dict:
        """
        Send multiple results to Google Apps Script in a single batch POST.
        
        Args:
            results: List of crawl result dictionaries
            
        Returns:
            Summary dict with success/failure counts
        """
        total = len(results)
        failed = 0
        successful = 0
        
        try:
            # Send all results as a single array in one POST
            response = self.session.post(
                self.script_url,
                json=results,  # Send entire list directly
                timeout=30,
                allow_redirects=True
            )
            
            if 200 <= response.status_code < 400:
                try:
                    resp_json = response.json()
                    if resp_json.get('success'):
                        successful = total
                        failed = 0
                        logger.info(f"✓ Sent batch of {total} rows to Google Sheet")
                    else:
                        failed = total
                        logger.warning(f"✗ Batch failed: {resp_json.get('error')}")
                except:
                    # If response is not JSON but status is good, assume success
                    successful = total
                    failed = 0
                    logger.info(f"✓ Sent batch of {total} rows to Google Sheet (HTTP {response.status_code})")
            else:
                failed = total
                logger.warning(f"✗ Batch failed with HTTP {response.status_code}")
                
        except Exception as e:
            failed = total
            logger.error(f"Error sending batch to Google Apps Script: {e}")
        
        summary = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"\nGoogle Apps Script Batch Summary:")
        logger.info(f"  Total: {total}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        
        return summary


def send_crawl_results_to_apps_script(results_file: str, script_url: str):
    """
    Send all results from a JSONL file to Google Apps Script.
    
    Args:
        results_file: Path to crawl_results.jsonl file
        script_url: URL of deployed Google Apps Script
    """
    try:
        results = []
        with open(results_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        
        integrator = GoogleAppsScriptIntegration(script_url)
        summary = integrator.send_batch(results)
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to send results: {e}")
        return None
