import random
import subprocess
import logging
import time
from typing import Tuple, Optional
from fake_useragent import UserAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VPNController:
    def __init__(self):
        """Initialize VPN controller with NordVPN CLI"""
        self.countries = [
            'us', 'uk', 'ca', 'au', 'fr', 'de', 'nl', 'se', 
            'no', 'ch', 'jp', 'sg'
        ]
        self.current_country = None
        self.ua = UserAgent()

    def _run_command(self, command: str) -> Tuple[int, str]:
        """Run shell command and return status and output"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True
            )
            return result.returncode, result.stdout
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return 1, str(e)

    def connect_vpn(self, country: Optional[str] = None) -> bool:
        """Connect to NordVPN using specified or random country"""
        if not country:
            country = random.choice(self.countries)
        
        logger.info(f"Connecting to NordVPN server in {country}...")
        status, output = self._run_command(f"nordvpn connect {country}")
        
        if status == 0:
            self.current_country = country
            logger.info(f"Successfully connected to {country}")
            return True
        else:
            logger.error(f"Failed to connect to VPN: {output}")
            return False

    def disconnect_vpn(self) -> bool:
        """Disconnect from NordVPN"""
        logger.info("Disconnecting from NordVPN...")
        status, output = self._run_command("nordvpn disconnect")
        
        if status == 0:
            self.current_country = None
            logger.info("Successfully disconnected from VPN")
            return True
        else:
            logger.error(f"Failed to disconnect from VPN: {output}")
            return False

    def get_random_user_agent(self) -> str:
        """Get random user agent string"""
        return self.ua.random

    def rotate_ip(self) -> bool:
        """Rotate IP by reconnecting to VPN"""
        if self.current_country:
            self.disconnect_vpn()
            time.sleep(2)  # Wait for disconnect
        return self.connect_vpn()

def get_headers() -> dict:
    """Get headers with random user agent"""
    vpn = VPNController()
    return {
        "User-Agent": vpn.get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

# Example usage
if __name__ == "__main__":
    vpn = VPNController()
    
    try:
        # Connect to random country
        if vpn.connect_vpn():
            print(f"Current headers: {get_headers()}")
            
            # Rotate IP after 5 minutes
            time.sleep(300)
            vpn.rotate_ip()
            
            print(f"New headers after rotation: {get_headers()}")
    except KeyboardInterrupt:
        print("\nStopping VPN rotation...")
    finally:
        vpn.disconnect_vpn()