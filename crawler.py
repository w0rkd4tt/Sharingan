import json
import hashlib
import os
import requests
import shutil
from tqdm import tqdm
import zipfile
import io
import sys
import logging
import time 
import argparse



def calculate_md5(file_path):
    """Calculate MD5 checksum of a file."""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def crawl_chaos_targets(output_file="chaos_domains.txt"):
    CHAOS_INDEX = "https://chaos-data.projectdiscovery.io/index.json"
    CHAOS_BASE_URL = "https://chaos-data.projectdiscovery.io"
    res = requests.get(CHAOS_INDEX)
    programs = res.json()

    all_domains = set()

    for program in tqdm(programs, desc="Downloading programs"):
        name = program.get("name")
        url = program.get("URL")  # .zip
        slug = url.split("/")[-1].replace(".zip", "")

        try:
            zip_res = requests.get(url)
            z = zipfile.ZipFile(io.BytesIO(zip_res.content))
            for file_name in z.namelist():
                if file_name.endswith(".txt"):
                    with z.open(file_name) as f:
                        domains = [line.decode("utf-8").strip() for line in f.readlines()]
                        all_domains.update(domains)
        except Exception as e:
            print(f"[!] Failed to download {slug}: {e}")

    # Save all domains
    with open(output_file, "w") as f:
        for domain in sorted(all_domains):
            f.write(domain + "\n")

    print(f"[+] Crawl complete. {len(all_domains)} domains saved to {output_file}")

def download_and_verify(url, local_filename):
    # Download the file
    if not os.path.exists(local_filename):
        # Tạo file JSON trống (dạng dictionary rỗng)
        with open(local_filename, 'w') as f:
            json.dump({}, f) 
    try:
        response = requests.get(url)
        with open('chaos-bugbounty-list.json', 'wb') as file:
            file.write(response.content)
    except Exception as e:
        print(e) 

    # Write the file to the local filesystem and calculate its checksum simultaneously
    md5_file1 = calculate_md5('chaos-bugbounty-list.json')
    md5_file2 = calculate_md5(local_filename)


    # Compare the calculated checksum with the expected checksum
    if md5_file1 == md5_file2:
        print("Checksum verification passed.")
        os.remove('chaos-bugbounty-list.json')
        return 
    else:
        print("Checksum verification failed.")
        os.remove(local_filename)
        try:
             shutil.copyfile('chaos-bugbounty-list.json', local_filename)   # Remove the corrupted or tampered file
             print("Update new file local")
        except Exception as e:
            print(e)
        return 




def get_tag_domain(local_filename):
    # Đọc dữ liệu từ tệp JSON
    with open(local_filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    results = []
    seen_domains = set()  # Dùng để check domain đã xử lý chưa

    # Duyệt qua từng chương trình trong dữ liệu
    for program in data['programs']:
        program_name = program.get('name')
        domains = program.get('domains', [])

        for domain in domains:
            if domain not in seen_domains:
                results.append({
                    'domain': domain,
                    'program': program_name
                })
                seen_domains.add(domain)  # Đánh dấu domain đã xử lý

    # Lưu kết quả vào tệp JSON mới
    with open('tagged_domains.json', 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile, indent=2, ensure_ascii=False)

    print(f"[+] Đã ghi {len(results)} domain duy nhất vào tagged_domains.json")
    

def map_domains(tagged_file, chaos_file, output_file):
    # Load tagged JSON
    with open(tagged_file, 'r') as f:
        tagged = json.load(f)

    # Load chaos domain từ TXT
    with open(chaos_file, 'r') as f:
        chaos_lines = [line.strip() for line in f if line.strip()]

    # Tạo danh sách kết quả
    result = []

    for domain in chaos_lines:
        program = None
        for tag in tagged:
            if tag["domain"] in domain:
                program = tag["program"]
                break
        result.append({
            "domain": domain,
            "program": program
        })

    # Ghi ra file JSON mới
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"[+] Đã ghi kết quả vào {output_file}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl and process chaos targets.")
    parser.add_argument("--update-target", action="store_true", help="Update chaos targets by crawling.")
    args = parser.parse_args()

    if args.update_target:
        crawl_chaos_targets()
    # Example usage:
    url = ' https://github.com/projectdiscovery/public-bugbounty-programs/raw/main/chaos-bugbounty-list.json'
    local_filename = 'local_chaos-bugbounty-list.json'

    try:
        download_and_verify(url, local_filename)
        get_tag_domain(local_filename)
        map_domains("tagged_domains.json", "chaos_domains.txt", "chaos_domain_tagged.json")
    except Exception as e:
        print(e)
