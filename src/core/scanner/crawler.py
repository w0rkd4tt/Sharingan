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
from pathlib import Path

class Crawler:
    def __init__(self, base_dir=None):
        """Initialize crawler with base directory for file operations"""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent
        self.database_dir = self.base_dir / "database"
        self.database_dir.mkdir(exist_ok=True)  # Create database dir if not exists
        self.CHAOS_INDEX = "https://chaos-data.projectdiscovery.io/index.json"
        self.CHAOS_BASE_URL = "https://chaos-data.projectdiscovery.io"
        self.BUGBOUNTY_URL = "https://github.com/projectdiscovery/public-bugbounty-programs/raw/main/chaos-bugbounty-list.json"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def calculate_md5(self, file_path):
        """Calculate MD5 checksum of a file."""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def crawl_chaos_targets(self, output_file="chaos_domains.txt"):
        """Crawl and save chaos targets to file"""
        try:
            res = requests.get(self.CHAOS_INDEX)
            programs = res.json()
        except Exception as e:
            self.logger.error(f"Failed to fetch chaos index: {e}")
            return False

        all_domains = set()
        
        for program in tqdm(programs, desc="Downloading programs"):
            name = program.get("name")
            url = program.get("URL")
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
                self.logger.error(f"Failed to download {slug}: {e}")

        output_path = self.base_dir / output_file
        with open(output_path, "w") as f:
            for domain in sorted(all_domains):
                f.write(domain + "\n")

        self.logger.info(f"Crawl complete. {len(all_domains)} domains saved to {output_file}")
        return True

    def download_and_verify(self, local_filename):
        """Download and verify bugbounty list"""
        local_path = self.database_dir / local_filename
        temp_file = self.database_dir / 'chaos-bugbounty-list.json'

        # Create empty JSON file if not exists
        if not local_path.exists():
            local_path.write_text("{}")

        try:
            response = requests.get(self.BUGBOUNTY_URL)
            temp_file.write_bytes(response.content)
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return False

        # Verify checksums
        md5_file1 = self.calculate_md5(temp_file)
        md5_file2 = self.calculate_md5(local_path)

        if md5_file1 == md5_file2:
            self.logger.info("Checksum verification passed.")
            temp_file.unlink()
            return True
        else:
            self.logger.warning("Checksum verification failed. Updating local file...")
            local_path.unlink()
            shutil.copy(temp_file, local_path)
            temp_file.unlink()
            return True

    def get_tag_domain(self, local_filename):
        """Extract and tag domains from local file"""
        try:
            with open(self.database_dir / local_filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as e:
            self.logger.error(f"Failed to read local file: {e}")
            return False

        results = []
        seen_domains = set()

        for program in data.get('programs', []):
            program_name = program.get('name')
            domains = program.get('domains', [])

            for domain in domains:
                if domain not in seen_domains:
                    results.append({
                        'domain': domain,
                        'program': program_name
                    })
                    seen_domains.add(domain)

        output_path = self.database_dir / 'tagged_domains.json'
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(results, outfile, indent=2, ensure_ascii=False)

        self.logger.info(f"Wrote {len(results)} unique domains to tagged_domains.json")
        return True

    def map_domains(self, tagged_file, chaos_file, output_file):
        """Map chaos domains to their programs"""
        try:
            # Load tagged domains
            with open(self.database_dir / tagged_file, 'r') as f:
                tagged = json.load(f)

            # Load chaos domains
            with open(self.database_dir / chaos_file, 'r') as f:
                chaos_lines = [line.strip() for line in f if line.strip()]

            # Map domains to programs
            result = []
            for domain in chaos_lines:
                program = next(
                    (tag["program"] for tag in tagged if tag["domain"] in domain),
                    None
                )
                result.append({
                    "domain": domain,
                    "program": program
                })

            # Write results
            with open(self.database_dir / output_file, 'w') as f:
                json.dump(result, f, indent=2)

            self.logger.info(f"Results written to {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to map domains: {e}")
            return False

# def main():
#     parser = argparse.ArgumentParser(description="Crawl and process chaos targets.")
#     parser.add_argument("--update-target", action="store_true", help="Update chaos targets by crawling.")
#     parser.add_argument("--base-dir", type=str, help="Base directory for file operations")
#     args = parser.parse_args()

#     crawler = Crawler(base_dir=args.base_dir)

#     if args.update_target:
#         crawler.crawl_chaos_targets()

#     try:
#         local_filename = 'local_chaos-bugbounty-list.json'
#         crawler.download_and_verify(local_filename)
#         crawler.get_tag_domain(local_filename)
#         crawler.map_domains("tagged_domains.json", "chaos_domains.txt", "chaos_domain_tagged.json")
#     except Exception as e:
#         logging.error(f"Error in main execution: {e}")

# if __name__ == "__main__":
#     main()
