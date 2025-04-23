import subprocess
import random
import time
from fake_useragent import UserAgent
from typing import Optional

class NordVPNRotator:
    def __init__(self):
        # Thêm danh sách server Việt Nam
        self.vietnam_servers = [
            'vn', 'vn#1', 'vn#2', 'vn#3', 'vn#4',
            'hanoi', 'hochiminh'
        ]
        
        self.countries = [
            'us', 'uk', 'de', 'fr', 'nl',
            'se', 'no', 'ca', 'jp', 'au'
        ]
        
        self.ua = UserAgent()
        self.vietnam_only = False  # Flag để chọn chỉ dùng server VN

    def set_vietnam_only(self, enabled: bool = True):
        """Bật/tắt chế độ chỉ dùng server Việt Nam."""
        self.vietnam_only = enabled
        print(f"[*] Chế độ chỉ dùng server Việt Nam: {'Bật' if enabled else 'Tắt'}")

    def run_command(self, cmd: list) -> Optional[str]:
        """Chạy command shell và return output."""
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.stdout.decode().strip()
        except subprocess.CalledProcessError as e:
            print(f"Lỗi khi chạy lệnh {' '.join(cmd)}")
            print(f"Error: {e.stderr.decode()}")
            return None

    def connect_vpn(self, country: str = None) -> bool:
        """Kết nối tới server NordVPN."""
        if not country:
            # Nếu bật chế độ VN only thì chỉ chọn từ server VN
            if self.vietnam_only:
                country = random.choice(self.vietnam_servers)
            else:
                country = random.choice(self.countries + self.vietnam_servers)
            
        print(f"[*] Đang kết nối tới NordVPN server ở {country}...")
        
        # Ngắt kết nối hiện tại nếu có
        self.run_command(['nordvpn', 'disconnect'])
        
        # Kết nối tới server mới
        result = self.run_command(['nordvpn', 'connect', country])
        if result and "connected" in result.lower():
            print(f"[+] Đã kết nối tới {country}")
            return True
        return False

    def get_current_ip(self) -> Optional[str]:
        """Lấy địa chỉ IP hiện tại."""
        result = self.run_command(['curl', 'ifconfig.me'])
        if result:
            print(f"[+] IP hiện tại: {result}")
            return result
        return None

    def get_random_user_agent(self) -> str:
        """Lấy random User-Agent."""
        user_agent = self.ua.random
        print(f"[+] User-Agent: {user_agent}")
        return user_agent

    def rotate_identity(self) -> tuple:
        """Đổi cả IP và User-Agent."""
        print("\n[*] Đang tạo identity mới...")
        
        # Đổi IP
        country = random.choice(self.countries)
        if not self.connect_vpn(country):
            print("[!] Không thể kết nối VPN")
            return None, None
            
        # Đợi vài giây để kết nối ổn định
        time.sleep(3)
        
        # Lấy IP mới và UA mới
        new_ip = self.get_current_ip()
        new_ua = self.get_random_user_agent()
        
        return new_ip, new_ua

# def main():
#     rotator = NordVPNRotator()
    
#     while True:
#         ip, ua = rotator.rotate_identity()
#         if ip and ua:
#             print("\n[+] Identity mới đã được tạo!")
#             print(f"IP: {ip}")
#             print(f"User-Agent: {ua}")
        
#         # Đợi 30 giây trước khi đổi identity mới
#         print("\n[*] Đợi 30 giây trước khi đổi identity...")
#         time.sleep(30)

# if __name__ == "__main__":
#     main()