#!/usr/bin/env python3
"""
Automatic kill switch when a remote mount goes bad.

Author: HabaneroSpices [admin@habanerospices.com]
Version: 1.0
"""

import os
import subprocess
import logging
import argparse
from pathlib import Path

import docker
from rich.logging import RichHandler

def parse_arguments():
    parser = argparse.ArgumentParser(description="Automatic kill switch when a remote mount goes bad.")
    parser.add_argument("mount_point", type=Path, help="Mount point")
    parser.add_argument(
        "label_name", 
        nargs='?',
        default="mount-kill-switch", 
        help="The label that the script will look for (default: mount-kill-switch)"
    )
    parser.add_argument("-v", "--verbose", action='count', default=0, help="show verbose log output.")
    parser.add_argument("-q", "--quiet", action='store_true', help="show only error log output.")
    parser.add_argument("--start", action='store_true', help="Start all containers matching the specified label")
    parser.add_argument("--stop", action='store_true', help="Stop all containers matching the specified label")
    return parser.parse_args()

def configure_logging(args):
    """Configure logging based on command line arguments."""
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose > 0:
        log_level = max(logging.DEBUG, logging.WARNING - args.verbose * 10)
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        datefmt="[%X]",
        handlers=[RichHandler()]
    )

def check_network_mount(mount_point):
    """Check if the network mount is accessible."""
    # TODO: add timeout, w/try-catch
    if not mount_point.is_mount():
        return False, f"Mount point {mount_point} does not exist"
    
    # TODO: add timeout, w/try-catch
    if not os.access(mount_point, os.R_OK):
        return False, f"Mount point {mount_point} is not accessible"
    
    try:
        result = subprocess.run(
            ['df', '-h', mount_point], capture_output=True, text=True, check=True
        )
        logging.debug(f"Mount details: {result.stdout}")
        return True, f"Mount point {mount_point} is accessible."
    except subprocess.CalledProcessError:
        return False, f"Error getting details for {mount_point}. It might not be mounted."

def get_labeled_containers(label):
    """Get Docker containers with the specified label."""
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"label": f"{label}=true"})
    return containers

def stop_labeled_containers(label):
    """Stop running containers with the specified label."""
    count = 0
    containers = get_labeled_containers(label) 
    for container in containers:
        if container.status == "running":
            logging.info(f"Stopping container: {container.name}")
            container.stop()
            count += 1
    return count

def start_labeled_containers(label):
    """Start running containers with the specified label."""
    count = 0
    containers = get_labeled_containers(label) 
    for container in containers:
        if container.status == "exited":
            logging.info(f"Starting container: {container.name}")
            container.start()
            count += 1
    return count

def main():
    """Main function to run the kill switch script."""
    args = parse_arguments()
    configure_logging(args)

    mount_point = args.mount_point.resolve()
    label_name = args.label_name

    """Temporary container administration"""
    if args.start:
        started_count = start_labeled_containers(label_name)
        if started_count > 0:
            logging.info(f"Started {started_count} containers with label '{label_name}'")
    elif args.stop:
        stopped_count = stop_labeled_containers(label_name)
        if stopped_count > 0:
            logging.info(f"Stopped {stopped_count} containers with label '{label_name}'")

    is_accessible, message = check_network_mount(mount_point)

    # TODO: add webhook
    if not is_accessible:
        logging.error(message)
        stopped_count = stop_labeled_containers(label_name)
        if stopped_count > 0:
            logging.info(f"Stopped {stopped_count} containers with label '{label_name}'")
    else:
        logging.info(message)
        """Disabled"""
#        started_count = start_labeled_containers(label_name)
#        if started_count > 0:
#            logging.info(f"Started {started_count} containers with label '{label_name}'")

if __name__ == "__main__":
    main()
