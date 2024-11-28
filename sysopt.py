```python
#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import logging
import datetime
import re
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemOptimizer:
    def __init__(self):
        self.backup_dir = Path('/var/backups/sysopt')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.modified_files: List[Path] = []

    def backup_file(self, filepath: Path) -> Path:
        backup_path = self.backup_dir / f"{filepath.name}_{self.timestamp}"
        shutil.copy2(filepath, backup_path)
        self.modified_files.append(filepath)
        return backup_path

    def restore_backups(self):
        for filepath in self.modified_files:
            backup = sorted(self.backup_dir.glob(f"{filepath.name}_*"))[-1]
            shutil.copy2(backup, filepath)
            logger.info(f"Restored {filepath} from backup {backup}")

    def optimize_fstab(self):
        fstab = Path('/etc/fstab')
        self.backup_file(fstab)

        content = fstab.read_text()
        ssd_options = "noatime,nodiratime,discard"
        tmpfs_entries = [
            f"tmpfs /tmp tmpfs defaults,noatime,mode=1777 0 0",
            f"tmpfs /var/log tmpfs defaults,noatime,mode=0755 0 0",
            f"tmpfs /var/spool tmpfs defaults,noatime,mode=1777 0 0",
            f"tmpfs /var/tmp tmpfs defaults,noatime,mode=1777 0 0"
        ]

        for line in content.splitlines():
            if any(mount in line for mount in ['/tmp', '/var/log', '/var/spool', '/var/tmp']):
                content = content.replace(line, '')

        content = content.strip() + '\n' + '\n'.join(tmpfs_entries)
        content = re.sub(r'(UUID=.*?\s+/\s+.*?\s+)([^\s]+)', f'\\1{ssd_options}', content)

        fstab.write_text(content)

    def optimize_sysctl(self):
        sysctl_conf = Path('/etc/sysctl.conf')
        self.backup_file(sysctl_conf)

        optimizations = {
            'net.core.rmem_max': '16777216',
            'net.core.wmem_max': '16777216',
            'net.ipv4.tcp_rmem': '4096 87380 16777216',
            'net.ipv4.tcp_wmem': '4096 87380 16777216',
            'net.ipv4.tcp_window_scaling': '1',
            'net.ipv4.tcp_timestamps': '1',
            'net.ipv4.tcp_mtu_probing': '1',
            'net.ipv4.tcp_base_mss': '1460',
            'net.ipv4.tcp_congestion_control': 'westwood+',
            'net.ipv4.tcp_slow_start_after_idle': '1',
            'net.ipv4.tcp_sack': '0',
            'net.ipv4.tcp_max_tw_buckets': '200000',
            'net.ipv4.tcp_max_orphans': '200000',
            'net.ipv4.udp_rmem_min': '4096',
            'net.ipv4.udp_wmem_min': '4096',
            'net.ipv4.udp_rmem_def': '87380',
            'net.ipv4.udp_wmem_def': '87380',
            'net.ipv4.udp_rmem_max': '16777216',
            'net.ipv4.udp_wmem_max': '16777216',
            'net.ipv4.udp_checksum': '1',
            'net.ipv4.udp_mem': '16777216 16777216 16777216',
            'net.ipv4.udp_frag': '1',
            'net.ipv4.udp_checksum_verify': '0',
            'net.ipv4.udp_timeout': '300',
            'net.core.netdev_max_backlog': '10000',
            'net.core.somaxconn': '1024',
            'net.ipv4.tcp_max_syn_backlog': '1024',
            'net.ipv4.tcp_tw_reuse': '1',
            'net.ipv4.tcp_tw_recycle': '1',
            'vm.dirty_ratio': '10',
            'vm.dirty_background_ratio': '5',
            'vm.swappiness': '10',
            'vm.vfs_cache_pressure': '50',
            'kernel.sched_latency_ns': '1000000',
            'kernel.sched_migration_cost_ns': '50000',
            'kernel.sched_min_granularity_ns': '1000000',
            'vm.overcommit_memory': '1',
            'vm.overcommit_ratio': '50',
            'fs.file-max': '1000000',
            'fs.nr_open': '1000000',
            'kernel.threads-max': '1000000',
            'vm.max_map_count': '262144'
        }

        content = '\n'.join(f"{k} = {v}" for k, v in optimizations.items())
        sysctl_conf.write_text(content)
        subprocess.run(['sysctl', '-p'], check=True)

    def optimize_grub(self):
        grub_default = Path('/etc/default/grub')
        self.backup_file(grub_default)

        grub_options = {
            'GRUB_CMDLINE_LINUX_DEFAULT': '"quiet elevator=deadline ibpb=off ibrs=off kpti=off l1tf=off mds=off mitigations=off no_stf_barrier noibpb noibrs nopcid nopti nospec_store_bypass_disable nospectre_v1 nospectre_v2 pcid=off pti=off spec_store_bypass_disable=off spectre_v2=off stf_barrier=off"',
            'GRUB_TIMEOUT': '2'
        }

        content = grub_default.read_text()
        for key, value in grub_options.items():
            content = re.sub(f'^{key}=.*$', f'{key}={value}', content, flags=re.MULTILINE)

        grub_default.write_text(content)
        subprocess.run(['update-grub'], check=True)

    def install_xanmod(self):
        commands = [
            'wget -qO - https://dl.xanmod.org/archive.key | gpg --dearmor -o /usr/share/keyrings/xanmod-archive-keyring.gpg',
            'echo "deb [signed-by=/usr/share/keyrings/xanmod-archive-keyring.gpg] http://deb.xanmod.org releases main" | tee /etc/apt/sources.list.d/xanmod-release.list',
            'apt update && apt install -y linux-xanmod-x64v3'
        ]

        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to execute: {cmd}")
                raise

    def run(self):
        try:
            if os.geteuid() != 0:
                raise PermissionError("Script must be run as root")

            logger.info("Starting system optimization")
            self.optimize_fstab()
            self.optimize_sysctl()
            self.optimize_grub()
            self.install_xanmod()
            logger.info("System optimization completed successfully")

            return True

        except Exception as e:
            logger.error(f"Error during optimization: {str(e)}")
            logger.info("Rolling back changes")
            self.restore_backups()
            return False

if __name__ == "__main__":
    optimizer = SystemOptimizer()
    success = optimizer.run()
    sys.exit(0 if success else 1)
```
