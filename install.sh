#!/bin/bash

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}"
cat << "EOF"
    ███████╗██╗  ██╗ █████╗ ██████╗ ██╗███╗   ██╗ ██████╗  █████╗ ███╗   ██╗
    ██╔════╝██║  ██║██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ ██╔══██╗████╗  ██║
    ███████╗███████║███████║██████╔╝██║██╔██╗ ██║██║  ███╗███████║██╔██╗ ██║
    ╚════██║██╔══██║██╔══██║██╔══██╗██║██║╚██╗██║██║   ██║██╔══██║██║╚██╗██║
    ███████║██║  ██║██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝██║  ██║██║ ╚████║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝
EOF
echo -e "${NC}"
echo "SharinganV2 - Cài đặt các công cụ cần thiết"
echo "=" * 80

# Kiểm tra và cài đặt Go nếu chưa có
if ! command -v go &> /dev/null; then
    echo -e "${YELLOW}[*] Đang cài đặt Go...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install go
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz
        sudo rm -rf /usr/local/go
        sudo tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz
        rm go1.21.6.linux-amd64.tar.gz
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
        source ~/.bashrc
    fi
fi

# Kiểm tra và cài đặt Python3 nếu chưa có
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[*] Đang cài đặt Python3...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python3
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install python3 python3-pip -y
    fi
fi

# Tạo thư mục tools nếu chưa tồn tại
mkdir -p tools
cd tools

# Cài đặt các công cụ Go
echo -e "${YELLOW}[*] Đang cài đặt các công cụ Go...${NC}"

# Katana
echo -e "${YELLOW}[*] Đang cài đặt Katana...${NC}"
go install github.com/projectdiscovery/katana/cmd/katana@latest

# Gau
echo -e "${YELLOW}[*] Đang cài đặt Gau...${NC}"
go install github.com/lc/gau/v2/cmd/gau@latest

# Hakrawler
echo -e "${YELLOW}[*] Đang cài đặt Hakrawler...${NC}"
go install github.com/hakluke/hakrawler@latest

# ParamSpider
echo -e "${YELLOW}[*] Đang cài đặt ParamSpider...${NC}"
git clone https://github.com/devanshbatham/ParamSpider.git
cd ParamSpider
pip3 install -r requirements.txt
cd ..

# Waybackurls
echo -e "${YELLOW}[*] Đang cài đặt Waybackurls...${NC}"
go install github.com/tomnomnom/waybackurls@latest

# Cài đặt các công cụ Python
echo -e "${YELLOW}[*] Đang cài đặt các công cụ Python...${NC}"

# Cài đặt các thư viện Python cần thiết
pip3 install requests beautifulsoup4 python-dotenv

# Tạo symbolic links cho các công cụ Go
echo -e "${YELLOW}[*] Đang tạo symbolic links...${NC}"
mkdir -p ~/go/bin
export PATH=$PATH:~/go/bin

# Kiểm tra cài đặt
echo -e "\n${GREEN}[+] Kiểm tra cài đặt:${NC}"
tools=("katana" "gau" "hakrawler" "waybackurls" "python3")
for tool in "${tools[@]}"; do
    if command -v $tool &> /dev/null; then
        echo -e "${GREEN}[+] $tool đã được cài đặt thành công${NC}"
    else
        echo -e "${RED}[-] $tool chưa được cài đặt${NC}"
    fi
done

echo -e "\n${GREEN}[+] Cài đặt hoàn tất!${NC}"
echo -e "${YELLOW}[*] Lưu ý: Bạn có thể cần khởi động lại terminal để các thay đổi có hiệu lực${NC}"
echo -e "${YELLOW}[*] Để sử dụng các công cụ, hãy đảm bảo ~/go/bin đã được thêm vào PATH${NC}"
echo -e "${YELLOW}[*] Thêm dòng sau vào ~/.bashrc hoặc ~/.zshrc:${NC}"
echo -e "    export PATH=\$PATH:~/go/bin" 