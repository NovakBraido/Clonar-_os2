#!/bin/bash

# Function to calculate MD5 hash of a device/file
calculate_hash() {
    local device=$1
    if [[ "$device" == *":"* ]]; then
        # For SSH, we need to run md5sum remotely
        local ssh_host=$(echo "$device" | cut -d':' -f1)
        local remote_device=$(echo "$device" | cut -d':' -f2)
        ssh "$ssh_host" "sudo md5sum $remote_device"
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

# Function to validate SSH connection and remote device
validate_ssh_device() {
    local ssh_host=$(echo "$1" | cut -d':' -f1)
    local remote_device=$(echo "$1" | cut -d':' -f2)
    
    if ! ssh -q "$ssh_host" exit; then
        echo "Error: Cannot connect to SSH host $ssh_host"
        exit 1
    fi
    
    if ! ssh "$ssh_host" "test -e $remote_device"; then
        echo "Error: Remote device $remote_device does not exist on $ssh_host"
        exit 1
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
echo "2. Remote via SSH"
read -p "Enter your choice (1/2): " CLONE_METHOD

case $CLONE_METHOD in
    1)
        # Local cloning
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
        # Remote cloning via SSH
        read -p "Enter source SSH host (e.g., user@remote-host): " SSH_HOST
        read -p "Enter source device on remote host (e.g., /dev/sda): " REMOTE_DEVICE
        SOURCE_DEVICE="$SSH_HOST:$REMOTE_DEVICE"
        validate_ssh_device "$SOURCE_DEVICE"
        
        read -p "Enter destination device (e.g., /dev/sdb): " DEST_DEVICE
        validate_local_device "$DEST_DEVICE"
        
        # Confirm operation
        echo "WARNING: This will ERASE ALL DATA on $DEST_DEVICE!"
        echo "Source: $SOURCE_DEVICE"
        echo "Destination: $DEST_DEVICE"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM
        
        if [ "$CONFIRM" != "yes" ]; then
            echo "Operation cancelled by user"
            exit 0
        fi
        
        # Calculate source hash before copying
        echo "Calculating source hash..."
        SOURCE_HASH=$(calculate_hash "$SOURCE_DEVICE")
        echo "Source hash: $SOURCE_HASH"
        
        # Perform the remote cloning
        echo "Starting remote cloning process..."
        ssh "$SSH_HOST" "sudo dd if=$REMOTE_DEVICE bs=4M" | dd of="$DEST_DEVICE" bs=4M status=progress conv=noerror,sync
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