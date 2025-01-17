#!/bin/bash

# Function to calculate MD5 hash of a device/file
calculate_hash() {
    local device=$1
    if [[ "$device" == *":"* ]]; then
        # For NFS mounted device
        local mount_point="/mnt/nfs_source"
        md5sum "$mount_point"
    else
        md5sum "$device"
    fi
}

# Function to validate local device
validate_local_device() {
    if [ ! -e "$1" ]; then
        echo "Error: Device $1 does not exist!"
        exit 1
    fi
}

# Function to setup NFS server
setup_nfs_server() {
    local nfs_server=$1
    local nfs_path=$2
    
    # Create exports directory if it doesn't exist
    ssh "root@$nfs_server" "mkdir -p $nfs_path"
    
    # Add export configuration if not already present
    ssh "root@$nfs_server" "grep -q '^$nfs_path' /etc/exports || echo '$nfs_path *(rw,sync,no_root_squash)' >> /etc/exports"
    
    # Restart NFS server
    ssh "root@$nfs_server" "exportfs -a && systemctl restart nfs-kernel-server"
    
    echo "NFS server configured successfully"
}

# Function to list available disks
list_disks() {
    local nfs_server=$1
    echo "Available disks on remote machine:"
    echo "--------------------------------"
    ssh "root@$nfs_server" "lsblk -d -o NAME,SIZE,MODEL | grep -v 'loop'"
    echo "--------------------------------"
}

# Function to validate and mount NFS share
validate_nfs_share() {
    local nfs_server=$1
    local nfs_path=$2
    local mount_point="/mnt/nfs_source"

    # Create mount point if it doesn't exist
    if [ ! -d "$mount_point" ]; then
        mkdir -p "$mount_point"
    fi

    # Test NFS server availability
    if ! ping -c 1 "$nfs_server" &> /dev/null; then
        echo "Error: Cannot reach NFS server $nfs_server"
        exit 1
    fi

    # Try to mount NFS share
    if ! mount -t nfs "$nfs_server:$nfs_path" "$mount_point"; then
        echo "Error: Cannot mount NFS share from $nfs_server:$nfs_path"
        exit 1
    fi

    echo "NFS share mounted successfully at $mount_point"
}

# Function to cleanup NFS mount
cleanup_nfs() {
    local mount_point="/mnt/nfs_source"
    if mountpoint -q "$mount_point"; then
        umount "$mount_point"
    fi
}

# Clear screen
clear

# Welcome message
echo "=== VM Cloning Tool ==="
echo "This tool will help you clone/mirror your virtual machine"
echo "----------------------------------------"

# Choose cloning method
echo "Select cloning method:"
echo "1. Local devices"
echo "2. Remote via NFS"
read -p "Enter your choice (1/2): " CLONE_METHOD

case $CLONE_METHOD in
    1)
        # Local cloning
        echo "Available local disks:"
        echo "--------------------------------"
        lsblk -d -o NAME,SIZE,MODEL | grep -v 'loop'
        echo "--------------------------------"
        
        read -p "Enter source device (e.g., /dev/sda): " SOURCE_DEVICE
        validate_local_device "$SOURCE_DEVICE"
        
        read -p "Enter destination device (e.g., /dev/sdb): " DEST_DEVICE
        validate_local_device "$DEST_DEVICE"
        
        # Confirm operation
        echo "WARNING: This will ERASE ALL DATA on $DEST_DEVICE!"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM
        
        if [ "$CONFIRM" != "yes" ]; then
            echo "Operation cancelled by user"
            exit 0
        fi
        
        # Calculate source hash before copying
        echo "Calculating source hash..."
        SOURCE_HASH=$(calculate_hash "$SOURCE_DEVICE")
        echo "Source hash: $SOURCE_HASH"
        
        # Perform the local cloning
        echo "Starting local cloning process..."
        dd if="$SOURCE_DEVICE" of="$DEST_DEVICE" bs=4M status=progress conv=noerror,sync
        ;;
        
    2)
        # Remote cloning via NFS
        read -p "Enter NFS server IP: " NFS_SERVER
        NFS_PATH="/exports/vm"
        
        # Setup NFS server
        echo "Setting up NFS server..."
        setup_nfs_server "$NFS_SERVER" "$NFS_PATH"
        
        # List available disks on remote machine
        list_disks "$NFS_SERVER"
        
        read -p "Enter source device from the list above (e.g., sda): " REMOTE_DEVICE
        REMOTE_DEVICE="/dev/$REMOTE_DEVICE"
        
        echo "Available local disks for destination:"
        echo "--------------------------------"
        lsblk -d -o NAME,SIZE,MODEL | grep -v 'loop'
        echo "--------------------------------"
        read -p "Enter destination device (e.g., /dev/sdb): " DEST_DEVICE

        validate_local_device "$DEST_DEVICE"
        validate_nfs_share "$NFS_SERVER" "$NFS_PATH"
        
        # Set source device path
        SOURCE_DEVICE="/mnt/nfs_source/$REMOTE_DEVICE"
        
        # Confirm operation
        echo "WARNING: This will ERASE ALL DATA on $DEST_DEVICE!"
        echo "Source: $SOURCE_DEVICE (via NFS)"
        echo "Destination: $DEST_DEVICE"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM
        
        if [ "$CONFIRM" != "yes" ]; then
            echo "Operation cancelled by user"
            cleanup_nfs
            exit 0
        fi
        
        # Calculate source hash before copying
        echo "Calculating source hash..."
        SOURCE_HASH=$(calculate_hash "$SOURCE_DEVICE")
        echo "Source hash: $SOURCE_HASH"
        
        # Perform the remote cloning
        echo "Starting remote cloning process..."
        dd if="$SOURCE_DEVICE" of="$DEST_DEVICE" bs=4M status=progress conv=noerror,sync
        
        # Cleanup NFS mount
        cleanup_nfs
        ;;
        
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac

# Calculate destination hash after copying
echo "Calculating destination hash..."
DEST_HASH=$(calculate_hash "$DEST_DEVICE")
echo "Destination hash: $DEST_HASH"

# Compare hashes
if [ "$SOURCE_HASH" = "$DEST_HASH" ]; then
    echo "Hash verification successful! Cloning completed successfully."
else
    echo "WARNING: Hash mismatch! The cloned drive may not be identical to the source."
    echo "Source hash: $SOURCE_HASH"
    echo "Destination hash: $DEST_HASH"
fi