import os
import subprocess
import netifaces

def run_command(command):
    """Runs a shell command and returns the output and error."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr.decode('utf-8')}")
        return None, e.stderr.decode('utf-8')

def get_network_interfaces():
    """Gets available network interfaces and their IP addresses."""
    interfaces = {}
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ip_info = addrs[netifaces.AF_INET][0]
            interfaces[iface] = ip_info['addr'], ip_info['netmask']
    return interfaces

def check_existing_mounts():
    """Checks for existing mounts."""
    print("Checking existing mounts...")
    stdout, stderr = run_command("mount | grep nfs")
    if stdout:
        print("NFS mounts found:")
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                print(f"Host: {parts[0]}, Host Folder: {parts[2]}")
    else:
        print("No NFS mounts found.")

def check_shared_folders_on_server():
    """Checks for shared folders on the NFS server."""
    print("Checking shared folders on NFS server...")
    stdout, stderr = run_command("sudo exportfs -v") # Requires sudo in a real environment
    if stdout:
        print("Shared folders found:")
        print(stdout)
    else:
        print("No shared folders found on the server.")

def find_nfs_servers_by_interface():
    """Discovers NFS servers on the network."""
    interfaces = get_network_interfaces()
    print("Select network interface to search for NFS servers:")
    for idx, (iface, (ip, mask)) in enumerate(interfaces.items(), start=1):
        print(f"{idx}. {iface} - {ip}/{mask}")

    try:
        choice = int(input("Enter the number of the desired interface: "))
        selected_iface = list(interfaces.items())[choice - 1]
        ip_network = selected_iface[1][0].rsplit('.', 1)[0] + ".0/24"

        print(f"Searching for NFS servers on network {ip_network}...")
        command = f"nmap -p 2049 --open {ip_network}"  # nmap is usually not available in WebContainer
        stdout, stderr = run_command(command)
        servers = []
        if stdout:
            for line in stdout.splitlines():
                if "Nmap scan report for" in line:
                    servers.append(line.split()[-1])
        if servers:
            print("NFS servers found:")
            for idx, server in enumerate(servers, start=1):
                print(f"{idx}. {server}")
            return servers
        else:
            print("No NFS servers found on the network.")
            return []
    except (ValueError, IndexError):
        print("Invalid interface selection.")
        return []


def verify_and_mount(server_ip, remote_dir, local_dir):
    """Verifies and mounts the NFS directory."""
    while True:
        # ... (Verification and mounting logic - same as before)
        break  # Exit the loop after successful mount or if the user cancels


def install_and_mount_nfs_client():
    """Installs and configures the NFS client."""
    # ... (Installation and mounting logic - same as before)

def install_and_configure_nfs_server():
    """Installs and configures the NFS server."""
    # ... (Installation and configuration logic - same as before)


def clone_disk_directly(source_disk, destination_disk):
    print(f"Simulating direct cloning from {source_disk} to {destination_disk}...")


def create_disk_image(source_disk, image_file):
    print(f"Simulating creation of image from {source_disk} to {image_file}...")
    with open(image_file, "w") as f:
        f.write("Simulated ISO image content")

def convert_image_to_gz(image_file, gz_file):
    print(f"Simulating conversion of {image_file} to {gz_file}...")
    with open(gz_file, "w") as f:
        f.write("Simulated GZ image content")


def transfer_image(gz_file, remote_dir):
    print(f"Simulating transfer of {gz_file} to {remote_dir}...")
    print("Arquivo iso.gz foi enviado para a outra máquina.")


def restore_image(gz_file, destination_disk):
    print(f"Simulating restoration of {gz_file} to {destination_disk}...")


def calculate_hash(file_path):
    print(f"Simulating hash calculation of {file_path}...")
    return "simulated_hash"


def disk_operations_menu():
    while True:
        print("\nDisk Operations:")
        print("1. Direct Clone")
        print("2. Create Image")
        print("3. Convert Image to .gz")
        print("4. Transfer Image via NFS")
        print("5. Restore Image")
        print("6. Calculate Hash") # Added hash calculation option
        print("7. Back to Main Menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            source_disk = input("Enter source disk: ")
            destination_disk = input("Enter destination disk: ")
            clone_disk_directly(source_disk, destination_disk)
        elif choice == '2':
            source_disk = input("Enter source disk: ")
            image_file = input("Enter image file name (e.g., image.iso): ")
            create_disk_image(source_disk, image_file)
        elif choice == '3':
            image_file = input("Enter image file name (e.g., image.iso): ")
            gz_file = input("Enter .gz file name (e.g., image.iso.gz): ")
            convert_image_to_gz(image_file, gz_file)
        elif choice == '4':
            gz_file = input("Enter .gz file name (e.g., image.iso.gz): ")
            remote_dir = input("Enter remote directory on NFS server: ")
            transfer_image(gz_file, remote_dir)
        elif choice == '5':
            gz_file = input("Enter .gz file name (e.g., image.iso.gz): ")
            destination_disk = input("Enter destination disk: ")
            restore_image(gz_file, destination_disk)
        elif choice == '6': # Handle hash calculation
            file_path = input("Enter file path to calculate hash: ")
            hash_value = calculate_hash(file_path)
            print(f"Calculated hash: {hash_value}")
        elif choice == '7':
            break
        else:
            print("Invalid choice.")


def main():
    print("Choose an action:")
    print("1. Install and configure NFS on the server")
    print("2. Install and configure NFS client")
    print("3. Check existing mounts")
    print("4. Check shared folders on server")
    print("5. Disk Operations") # Renamed for clarity
    print("6. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        install_and_configure_nfs_server()
    elif choice == "2":
        install_and_mount_nfs_client()
    elif choice == "3":
        check_existing_mounts()
    elif choice == "4":
        check_shared_folders_on_server()
    elif choice == "5":
        disk_operations_menu()
    elif choice == "6":
        print("Exiting...")
    else:
        print("Invalid choice. Try again.")

if __name__ == "__main__":
    try:
        import netifaces
    except ImportError:
        print("The 'netifaces' module is not installed. Install it with 'pip install netifaces'.  "
              "Note: pip is not available in WebContainer.")
        exit(1)
    main()
