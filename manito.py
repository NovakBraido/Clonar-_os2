import os
import subprocess
import netifaces
import shutil

def run_command(command):
    """Executa um comando no shell e retorna a saída."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando: {e.stderr.decode('utf-8')}")
        return None, e.stderr.decode('utf-8')

def get_network_interfaces():
    """Obtém todas as interfaces de rede disponíveis e seus endereços IP."""
    interfaces = {}
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ip_info = addrs[netifaces.AF_INET][0]
            interfaces[iface] = ip_info['addr'], ip_info['netmask']
    return interfaces

def check_existing_mounts():
    """Verifica se já existem servidores montados ou pastas compartilhadas no cliente."""
    print("Verificando montagens existentes...")
    stdout, stderr = run_command("mount | grep nfs")
    if stdout:
        print("Montagens NFS encontradas:")
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                print(f"Host: {parts[0]}, Pasta do Host: {parts[2]}")
    else:
        print("Nenhuma montagem NFS encontrada.")


def check_shared_folders_on_server():
    """Verifica se há pastas compartilhadas no servidor NFS."""
    print("Verificando pastas compartilhadas no servidor NFS...")
    stdout, stderr = run_command("sudo exportfs -v")
    if stdout:
        print("Pastas compartilhadas encontradas:")
        print(stdout)
    else:
        print("Nenhuma pasta compartilhada encontrada no servidor.")

def find_nfs_servers_by_interface():
    """Descobre servidores NFS com base nas interfaces de rede disponíveis."""
    interfaces = get_network_interfaces()
    print("Selecione a interface de rede para buscar servidores NFS:")
    for idx, (iface, (ip, mask)) in enumerate(interfaces.items(), start=1):
        print(f"{idx}. {iface} - {ip}/{mask}")

    choice = int(input("Digite o número da interface desejada: "))
    selected_iface = list(interfaces.items())[choice - 1]
    ip_network = selected_iface[1][0].rsplit('.', 1)[0] + ".0/24"

    print(f"Procurando servidores NFS na rede {ip_network}...")
    command = f"nmap -p 2049 --open {ip_network}"
    stdout, stderr = run_command(command)
    servers = []
    if stdout:
        for line in stdout.splitlines():
            if "Nmap scan report for" in line:
                servers.append(line.split()[-1])
    if servers:
        print("Servidores NFS encontrados:")
        for idx, server in enumerate(servers, start=1):
            print(f"{idx}. {server}")
        return servers
    else:
        print("Nenhum servidor NFS encontrado na rede.")
        return []

def verify_and_mount(server_ip, remote_dir, local_dir):
    """Verifica e monta o diretório NFS."""
    while True:
        # Verifica se o diretório remoto existe no servidor
        check_command = f"sudo showmount -e {server_ip}"
        stdout, stderr = run_command(check_command)
        if stderr:
            print(f"Erro ao verificar o servidor: {stderr}")
            server_ip = input("Digite novamente o IP do servidor: ")
            continue
        if remote_dir not in stdout:
            print(f"O diretório remoto {remote_dir} não existe no servidor {server_ip}.")
            remote_dir = input("Digite um diretório remoto válido no servidor: ")
            continue

        # Verifica ou cria o diretório local
        try:
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            else:
                print(f"O diretório local {local_dir} já existe. Usando-o para montagem.")
        except PermissionError:
            print(f"Permissão negada ao acessar ou criar {local_dir}. Verifique as permissões.")
            local_dir = input("Digite um novo diretório local válido para montagem: ")
            continue
        except FileExistsError:
            print(f"O diretório {local_dir} já existe, mas há um problema com sua estrutura. Verifique.")
            local_dir = input("Digite um novo diretório local válido para montagem: ")
            continue

        # Tenta montar o diretório
        mount_command = f"sudo mount -t nfs {server_ip}:{remote_dir} {local_dir}"
        stdout, stderr = run_command(mount_command)
        if stderr:
            print(f"Erro ao montar o NFS: {stderr}")
            local_dir = input("Digite um diretório local válido para montagem: ")
        else:
            print(f"NFS montado com sucesso em {local_dir}.")
            break

def install_and_mount_nfs_client():
    """Instala e configura o cliente NFS."""
    print("Instalando o cliente NFS...")
    commands = [
        "sudo apt update",
        "sudo apt install -y nfs-common"
    ]
    for command in commands:
        stdout, stderr = run_command(command)
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

    servers = find_nfs_servers_by_interface()

    if not servers:
        print("Nenhum servidor NFS disponível para montar.")
        return

    print("Selecione um servidor NFS para montar:")
    for idx, server in enumerate(servers, start=1):
        print(f"{idx}. {server}")

    choice = int(input("Digite o número do servidor desejado: "))
    server_ip = servers[choice - 1]
    remote_dir = input("Digite o diretório remoto no servidor (ex.: /srv): ")
    local_dir = input("Digite o diretório local para montagem (ex.: /mnt/nfs): ")

    verify_and_mount(server_ip, remote_dir, local_dir)

def copiar_disco_e_compactar(disco_origem):
    """Copia um disco, converte para .iso e .gz, e oferece opções de NFS."""

    nome_arquivo_iso = os.path.basename(disco_origem) + ".iso"
    nome_arquivo_gz = nome_arquivo_iso + ".gz"

    try:
        # 1. Criar a imagem ISO (mkisofs)
        print(f"Criando imagem ISO: {nome_arquivo_iso}")
        subprocess.run(["mkisofs", "-o", nome_arquivo_iso, disco_origem], check=True)

        # 2. Compactar a imagem ISO (gzip)
        print(f"Compactando imagem ISO: {nome_arquivo_gz}")
        subprocess.run(["gzip", nome_arquivo_iso], check=True)

        # Listar mounts NFS (findmnt)
        try:
            mounts = subprocess.check_output(['findmnt', '-t', 'nfs']).decode().splitlines()
            nfs_options = {}
            for i, mount in enumerate(mounts):
                if 'on' in mount:
                    parts = mount.split('on')
                    nfs_options[i+1] = parts[1].split(' ')[1]
        except FileNotFoundError:
            print("O comando 'findmnt' não foi encontrado. Certifique-se de que esteja instalado.")
            return
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar findmnt: {e}")
            return


        if not nfs_options:
            print("Nenhum compartilhamento NFS encontrado.")
            return

        print("Compartilhamentos NFS disponíveis:")
        for i, path in nfs_options.items():
            print(f"{i}. {path}")

        while True:
            try:
                escolha = int(input("Escolha o número do compartilhamento NFS de destino: "))
                if escolha in nfs_options:
                    destino_nfs = nfs_options[escolha]
                    break
                else:
                    print("Escolha inválida.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

        caminho_nfs = os.path.join(destino_nfs, nome_arquivo_gz)

        # 3. Copiar para o NFS (cp)
        print(f"Copiando para NFS: {caminho_nfs}")
        shutil.copy2(nome_arquivo_gz, caminho_nfs) # Mantém metadados com copy2

        print("Operação concluída com sucesso!")

    except subprocess.CalledProcessError as e:
        print(f"Erro durante a execução do comando: {e}")
    except FileNotFoundError:
        print(f"Disco de origem não encontrado: {disco_origem}")
    except Exception as e:
        print(f"Erro inesperado: {e}")


# Exemplo de uso (adapte o caminho conforme necessário)
disco_origem = input("Digite o caminho do disco de origem (ex: /dev/sda): ")
copiar_disco_e_compactar(disco_origem)

def install_and_configure_nfs_server():
    """Instala e configura o NFS no servidor."""
    print("Instalando e configurando o NFS no servidor...")
    commands = [
        "sudo apt update",
        "sudo apt install -y nfs-kernel-server",
        "sudo systemctl enable nfs-kernel-server",
        "sudo systemctl start nfs-kernel-server"
    ]
    for command in commands:
        stdout, stderr = run_command(command)
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

    print("Configuração do diretório NFS...")
    mount_point = input("Digite o caminho do dispositivo para montar (ex.: /dev/sda1): ")
    mount_target = "/srv"

    stdout, stderr = run_command(f"sudo mount -t ext4 {mount_point} {mount_target}")
    if stderr:
        print(f"Erro ao montar o dispositivo: {stderr}")
        return

    interfaces = get_network_interfaces()
    print("Selecione a interface de rede para configurar o NFS:")
    for idx, (iface, (ip, mask)) in enumerate(interfaces.items(), start=1):
        print(f"{idx}. {iface} - {ip}/{mask}")

    choice = int(input("Digite o número da interface desejada: "))
    selected_iface = list(interfaces.items())[choice - 1]
    ip_network = selected_iface[1][0].rsplit('.', 1)[0] + ".0/24"

    exports_path = "/etc/exports"

    # Verifica se a rede já está no /etc/exports
    with open(exports_path, 'r') as f:
        exports_content = f.readlines()

    export_line = f"{mount_target} {ip_network}(rw,no_root_squash,sync)\n"
    if export_line in exports_content:
        print(f"A rede {ip_network} já está configurada no /etc/exports.")
    else:
        with open(exports_path, 'a') as f:
            f.write(export_line)
        print(f"Linha adicionada ao /etc/exports: {export_line.strip()}")

    run_command("sudo exportfs -ra")
    run_command("sudo systemctl restart nfs-kernel-server")
    print("NFS configurado com sucesso e disponível para a rede.")

def main():
    print("Escolha uma ação:")
    print("1. Instalar e configurar o NFS no servidor")
    print("2. Instalar e configurar o cliente NFS")
    print("3. Verificar montagens existentes")
    print("4. Verificar pastas compartilhadas no servidor")
    print("5. Opções De Clonagem")
    print("6. Sair")

    choice = input("Digite o número da sua escolha: ")

    if choice == "1":
        install_and_configure_nfs_server()
    elif choice == "2":
        install_and_mount_nfs_client()
    elif choice == "3":
        check_existing_mounts()
    elif choice == "4":
        check_shared_folders_on_server()
    elif choice == "5":
        copiar_disco_e_compactar()
    elif choice == "6":
        print("Saindo...")
    else:
        print("Escolha inválida. Tente novamente.")

if __name__ == "__main__":
    try:
        import netifaces
    except ImportError:
        print("O módulo 'netifaces' não está instalado. Instale-o com 'pip install netifaces'.")
        exit(1)
    main()
