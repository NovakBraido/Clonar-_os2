import subprocess
import netifaces
import os
import hashlib

def executar_comando(comando):
    try:
        result = subprocess.run(comando, shell=True, check=True, capture_output=True, text=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando: {e.stderr}")
        return None, e.stderr

def obter_interfaces_de_rede():
    interfaces = {}
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ip_info = addrs[netifaces.AF_INET][0]
            interfaces[iface] = ip_info['addr'], ip_info['netmask']
    return interfaces

def verificar_montagens_existentes():
    print("Verificando montagens existentes...")
    stdout, stderr = executar_comando("mount | grep nfs")
    if stdout:
        print("Montagens NFS encontradas:")
        print(stdout)
    elif stderr:
        print(f"Erro: {stderr}")
    else:
        print("Nenhuma montagem NFS encontrada.")

def verificar_pastas_compartilhadas():
    print("Verificando pastas compartilhadas no servidor NFS...")
    stdout, stderr = executar_comando("sudo exportfs -v")
    if stdout:
        print("Pastas compartilhadas encontradas:")
        print(stdout)
    elif stderr:
        print(f"Erro: {stderr}")
    else:
        print("Nenhuma pasta compartilhada encontrada no servidor.")

def encontrar_servidores_nfs(ip_rede):
    print(f"Procurando servidores NFS na rede {ip_rede}...")
    stdout, stderr = executar_comando(f"nmap -p 2049 --open {ip_rede}")
    if stdout:
        servidores = []
        for linha in stdout.splitlines():
            if "Nmap scan report for" in linha:
                servidores.append(linha.split()[-1])
        if servidores:
            print("Servidores NFS encontrados:")
            for i, servidor in enumerate(servidores, 1):
                print(f"{i}. {servidor}")
            return servidores
        else:
            print("Nenhum servidor NFS encontrado na rede.")
            return []
    elif stderr:
        print(f"Erro: {stderr}")
        return []

def verificar_e_montar(ip_servidor, dir_remoto, dir_local):
    while True:
        stdout, stderr = executar_comando(f"sudo showmount -e {ip_servidor}")
        if stderr:
            print(f"Erro ao verificar o servidor: {stderr}")
            ip_servidor = input("Digite novamente o IP do servidor: ")
            continue

        if not stdout or dir_remoto not in stdout:
            print(f"O diretório remoto '{dir_remoto}' não existe no servidor {ip_servidor}.")
            dir_remoto = input("Digite um diretório remoto válido: ")
            continue

        if not os.path.exists(dir_local):
            try:
                os.makedirs(dir_local)
            except OSError as e:
                print(f"Erro ao criar o diretório local: {e}")
                dir_local = input("Digite um novo diretório local: ")
                continue

        stdout, stderr = executar_comando(f"sudo mount -t nfs {ip_servidor}:{dir_remoto} {dir_local}")
        if stderr:
            print(f"Erro ao montar o NFS: {stderr}")
            dir_local = input("Digite um novo diretório local: ")
            continue
        else:
            print(f"NFS montado com sucesso em {dir_local}")
            break

def instalar_cliente_nfs():
    print("Instalando cliente NFS...")
    stdout, stderr = executar_comando("sudo apt update && sudo apt install -y nfs-common")
    if stdout:
        print(stdout)
    if stderr:
        print(f"Erro durante a instalação: {stderr}")
        return False
    return True

def configurar_servidor_nfs():
    print("Configurando servidor NFS...")
    stdout, stderr = executar_comando("sudo apt update && sudo apt install -y nfs-kernel-server")
    if stdout:
        print(stdout)
    if stderr:
        print(f"Erro durante a instalação: {stderr}")
        return

    mount_point = input("Digite o caminho do dispositivo para montar (ex.: /dev/sda1): ")
    mount_target = "/srv"

    stdout, stderr = executar_comando(f"sudo mkdir -p {mount_target} && sudo mount -t ext4 {mount_point} {mount_target}")
    if stderr:
        print(f"Erro ao criar ou montar o diretório: {stderr}")
        return

    interfaces = obter_interfaces_de_rede()
    if not interfaces:
        print("Nenhuma interface de rede encontrada.")
        return

    print("Selecione a interface de rede para configurar o NFS:")
    for i, (iface, (ip, mask)) in enumerate(interfaces.items(), 1):
        print(f"{i}. {iface} - {ip}/{mask}")

    while True:
        try:
            escolha = int(input("Digite o número da interface desejada: "))
            selected_iface = list(interfaces.items())[escolha - 1]
            ip_rede = selected_iface[1][0].rsplit('.', 1)[0] + ".0/24"
            break
        except (ValueError, IndexError):
            print("Escolha inválida. Tente novamente.")

    exports_path = "/etc/exports"
    export_line = f"{mount_target} {ip_rede}(rw,sync,no_subtree_check)\n"

    try:
        with open(exports_path, 'r') as f:
            exports_content = f.read()
        if export_line not in exports_content:
            with open(exports_path, 'a') as f:
                f.write(export_line)
            print(f"Linha adicionada ao /etc/exports: {export_line.strip()}")
    except OSError as e:
        print(f"Erro ao escrever em /etc/exports: {e}")
        return

    stdout, stderr = executar_comando("sudo exportfs -ra && sudo systemctl restart nfs-kernel-server")
    if stdout:
        print(stdout)
    if stderr:
        print(f"Erro ao reiniciar o servidor NFS: {stderr}")

def clonar_disco(disco_origem, disco_destino):
    print(f"Clonando disco de {disco_origem} para {disco_destino}...")
    stdout, stderr = executar_comando(f"sudo dd if={disco_origem} of={disco_destino} bs=4M status=progress conv=sync,noerror")
    if stdout:
        print(stdout)
    if stderr:
        print(f"Erro durante a clonagem: {stderr}")

def criar_imagem_disco(disco_origem, arquivo_imagem):
    print(f"Criando imagem de disco de {disco_origem} em {arquivo_imagem}...")
    stdout, stderr = executar_comando(f"sudo dd if={disco_origem} of={arquivo_imagem} bs=4M status=progress conv=sync,noerror")
    if stdout:
        print(stdout)
    if stderr:
        print(f"Erro durante a criação da imagem: {stderr}")

def converter_imagem_para_gz(arquivo_imagem, arquivo_gz):
    print(f"Convertendo imagem {arquivo_imagem} para {arquivo_gz}...")
    stdout, stderr = executar_comando(f"gzip -c {arquivo_imagem} > {arquivo_gz}")
    if stderr:
        print(f"Erro durante a compressão: {stderr}")

def transferir_imagem(arquivo_gz, dir_remoto):
    print(f"Transferindo imagem {arquivo_gz} para {dir_remoto}...")
    stdout, stderr = executar_comando(f"cp {arquivo_gz} {dir_remoto}")
    if stdout:
        print(stdout)
    if stderr:
        print(f"Erro durante a transferência: {stderr}")

def restaurar_imagem(arquivo_gz, disco_destino):
    print(f"Restaurando imagem {arquivo_gz} para {disco_destino}...")
    stdout, stderr = executar_comando(f"gunzip -c {arquivo_gz} | sudo dd of={disco_destino} bs=4M status=progress conv=sync,noerror")
    if stdout:
        print(stdout)
    if stderr:
        print(f"Erro durante a restauração: {stderr}")

def calcular_hash(caminho_arquivo):
    try:
        with open(caminho_arquivo, "rb") as f:
            conteudo = f.read()
        hash_md5 = hashlib.md5(conteudo).hexdigest()
        print(f"Hash MD5 de '{caminho_arquivo}': {hash_md5}")
        return hash_md5
    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho_arquivo}' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao calcular o hash: {e}")
        return None

def menu_operacoes_disco():
    while True:
        print("\nOperações de Disco:")
        print("1. Clonar Disco")
        print("2. Criar Imagem")
        print("3. Converter Imagem para .gz")
        print("4. Transferir Imagem via NFS")
        print("5. Restaurar Imagem")
        print("6. Calcular Hash")
        print("7. Voltar ao Menu Principal")

        escolha = input("Digite sua escolha: ")

        if escolha == '1':
            disco_origem = input("Digite o disco de origem: ")
            disco_destino = input("Digite o disco de destino: ")
            clonar_disco(disco_origem, disco_destino)
        elif escolha == '2':
            disco_origem = input("Digite o disco de origem: ")
            arquivo_imagem = input("Digite o nome do arquivo de imagem (ex.: imagem.iso): ")
            criar_imagem_disco(disco_origem, arquivo_imagem)
        elif escolha == '3':
            arquivo_imagem = input("Digite o nome do arquivo de imagem (ex.: imagem.iso): ")
            arquivo_gz = input("Digite o nome do arquivo .gz (ex.: imagem.iso.gz): ")
            converter_imagem_para_gz(arquivo_imagem, arquivo_gz)
        elif escolha == '4':
            arquivo_gz = input("Digite o nome do arquivo .gz (ex.: imagem.iso.gz): ")
            dir_remoto = input("Digite o diretório remoto no servidor NFS: ")
            transferir_imagem(arquivo_gz, dir_remoto)
        elif escolha == '5':
            arquivo_gz = input("Digite o nome do arquivo .gz (ex.: imagem.iso.gz): ")
            disco_destino = input("Digite o disco de destino: ")
            restaurar_imagem(arquivo_gz, disco_destino)
        elif escolha == '6':
            caminho_arquivo = input("Digite o caminho do arquivo para calcular o hash: ")
            calcular_hash(caminho_arquivo)
        elif escolha == '7':
            break
        else:
            print("Escolha inválida.")


def menu_principal():
    while True:
        print("\nEscolha uma ação:")
        print("1. Configurar servidor NFS")
        print("2. Instalar cliente NFS")
        print("3. Verificar montagens")
        print("4. Verificar pastas compartilhadas")
        print("5. Operações de Disco")
        print("6. Sair")

        escolha = input("Digite sua escolha: ")

        if escolha == '1':
            configurar_servidor_nfs()
        elif escolha == '2':
            instalar_cliente_nfs()
        elif escolha == '3':
            verificar_montagens_existentes()
        elif escolha == '4':
            verificar_pastas_compartilhadas()
        elif escolha == '5':
            menu_operacoes_disco()
        elif escolha == '6':
            print("Saindo...")
            break
        else:
            print("Escolha inválida.")

if __name__ == "__main__":
    menu_principal()
