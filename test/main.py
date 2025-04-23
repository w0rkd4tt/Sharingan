import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.vpn import NordVPNRotator
from src.core.scanner import Scanner, Crawler
from src.core.chaos import ChaosScanner
from src.core.notification import TelegramNotifier

class TargetScanner:
    def __init__(
        self,
        burp_api_url: str,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        base_dir: Optional[str] = None
    ):
        """Initialize TargetScanner with all necessary components"""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        # Initialize components
        self.vpn = NordVPNRotator()
        self.scanner = Scanner(burp_api_url, bot_token, chat_id)
        self.crawler = Crawler(base_dir)
        self.chaos = ChaosScanner(base_dir)
        self.notifier = TelegramNotifier(bot_token, chat_id) if bot_token and chat_id else None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def scan_targets(
        self,
        target_urls: List[str],
        scan_configs: List[str],
        use_vpn: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform complete scan of target URLs with VPN rotation
        
        Args:
            target_urls: List of URLs to scan
            scan_configs: List of scan configuration names
            use_vpn: Whether to use VPN rotation
            username: Optional login username
            password: Optional login password
        
        Returns:
            Dict containing scan results and statistics
        """
        results = {
            "successful_scans": [],
            "failed_scans": [],
            "total_vulnerabilities": 0,
            "scan_time": 0
        }

        for url in target_urls:
            try:
                self.logger.info(f"Starting scan for {url}")
                
                # Rotate VPN if enabled
                if use_vpn:
                    self.logger.info("Rotating VPN connection")
                    if not self.vpn.rotate_identity():
                        self.logger.error("Failed to rotate VPN")
                        results["failed_scans"].append({"url": url, "reason": "VPN rotation failed"})
                        continue

                # Run the scan
                scan_id = self.scanner.create_scan([url], scan_configs, username, password)
                if not scan_id:
                    self.logger.error(f"Failed to create scan for {url}")
                    results["failed_scans"].append({"url": url, "reason": "Scan creation failed"})
                    continue

                # Monitor scan progress
                success = self.scanner.run_scan([url], scan_configs, username, password)
                
                if success:
                    self.logger.info(f"Scan completed successfully for {url}")
                    results["successful_scans"].append(url)
                else:
                    self.logger.error(f"Scan failed for {url}")
                    results["failed_scans"].append({"url": url, "reason": "Scan execution failed"})

            except Exception as e:
                self.logger.error(f"Error scanning {url}: {e}")
                results["failed_scans"].append({"url": url, "reason": str(e)})

        return results

    def discover_targets(self) -> List[str]:
        """
        Discover potential target URLs using Chaos and Crawler
        
        Returns:
            List of discovered target URLs
        """
        try:
            # Crawl chaos targets
            self.chaos.crawl_chaos_targets()
            
            # Process and tag domains
            self.crawler.download_and_verify('local_chaos-bugbounty-list.json')
            self.crawler.get_tag_domain('local_chaos-bugbounty-list.json')
            self.crawler.map_domains(
                "tagged_domains.json",
                "chaos_domains.txt",
                "chaos_domain_tagged.json"
            )
            
            # Read and return discovered targets
            with open(self.base_dir / "chaos_domain_tagged.json") as f:
                targets = [domain["domain"] for domain in json.load(f)]
            
            return targets
            
        except Exception as e:
            self.logger.error(f"Error discovering targets: {e}")
            return []

def main():
    """Example usage of TargetScanner"""
    import argparse
    from dotenv import load_dotenv
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Target Scanner with optional crawling and VPN")
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="Enable target discovery through crawling"
    )
    parser.add_argument(
        "--target-urls",
        nargs="+",
        help="List of target URLs to scan",
        default=[]
    )
    parser.add_argument(
        "--max-targets",
        type=int,
        default=5,
        help="Maximum number of targets to scan (default: 5)"
    )
    parser.add_argument(
        "--use-vpn",
        action="store_true",
        help="Enable VPN rotation during scanning"
    )
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize scanner
    scanner = TargetScanner(
        burp_api_url=os.getenv('BURP_API_URL'),
        bot_token=os.getenv('BOT_TOKEN'),
        chat_id=os.getenv('CHAT_ID')
    )
    
    # Get targets either from crawling or command line
    targets = []
    if args.crawl:
        scanner.logger.info("Starting target discovery through crawling...")
        targets = scanner.discover_targets()
        scanner.logger.info(f"Discovered {len(targets)} targets")
    
    # Add any manually specified targets
    targets.extend(args.target_urls)
    
    if not targets:
        scanner.logger.error("No targets specified. Use --crawl or --target-urls")
        return
    
    # Limit number of targets
    targets = targets[:args.max_targets]
    scanner.logger.info(f"Scanning {len(targets)} targets")
    scanner.logger.info(f"VPN rotation is {'enabled' if args.use_vpn else 'disabled'}")
    
    # Scan targets
    results = scanner.scan_targets(
        target_urls=targets,
        scan_configs=["Checking"],
        use_vpn=args.use_vpn
    )
    
    # Print results
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()


