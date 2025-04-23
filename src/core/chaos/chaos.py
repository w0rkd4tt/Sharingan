import requests
import zipfile
import io
import os
import logging
from pathlib import Path
from tqdm import tqdm

class ChaosScanner:
    def __init__(self, base_dir=None):
        """Initialize ChaosScanner with base directory for file operations"""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent
        self.database_dir = self.base_dir / "database"
        self.database_dir.mkdir(exist_ok=True)  # Create database dir if not exists
        
        self.CHAOS_INDEX = "https://chaos-data.projectdiscovery.io/index.json"
        self.CHAOS_BASE_URL = "https://chaos-data.projectdiscovery.io"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def crawl_chaos_targets(self, output_file="chaos_domains.txt"):
        """
        Crawl and download chaos targets
        Args:
            output_file: Name of file to save domains to
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("Starting chaos targets crawl")
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
                domains = self._process_program_zip(url)
                all_domains.update(domains)
                self.logger.debug(f"Successfully processed {name}: {len(domains)} domains")
            except Exception as e:
                self.logger.error(f"Failed to download {slug}: {e}")
                continue

        if all_domains:
            self._save_domains(all_domains, output_file)
            return True
        return False

    def _process_program_zip(self, url):
        """
        Process a program's zip file and extract domains
        Args:
            url: URL of the zip file to process
        Returns:
            set: Set of domains found in the zip file
        """
        domains = set()
        zip_res = requests.get(url)
        z = zipfile.ZipFile(io.BytesIO(zip_res.content))
        
        for file_name in z.namelist():
            if file_name.endswith(".txt"):
                with z.open(file_name) as f:
                    domains.update(
                        line.decode("utf-8").strip() 
                        for line in f.readlines()
                    )
        return domains

    def _save_domains(self, domains, output_file):
        """
        Save domains to file
        Args:
            domains: Set of domains to save
            output_file: Name of output file
        """
        output_path = self.database_dir / output_file
        with open(output_path, "w") as f:
            for domain in sorted(domains):
                f.write(f"{domain}\n")
        
        self.logger.info(
            f"Crawl complete. {len(domains)} domains saved to {output_file}"
        )

def main():
    """Main entry point for command line usage"""
    import argparse
    parser = argparse.ArgumentParser(description="Crawl chaos targets")
    parser.add_argument(
        "--output", 
        default="chaos_domains.txt",
        help="Output file name"
    )
    parser.add_argument(
        "--dir",
        help="Base directory for file operations"
    )
    args = parser.parse_args()

    scanner = ChaosScanner(base_dir=args.dir)
    scanner.crawl_chaos_targets(args.output)

if __name__ == "__main__":
    main()
