import requests
import zipfile
import io
import os
from tqdm import tqdm


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

if __name__ == "__main__":
    crawl_chaos_targets()
