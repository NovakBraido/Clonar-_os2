#!/bin/bash

# Função para calcular o hash MD5 de um dispositivo/arquivo
calculate_hash() {
    local device=$1
    if [[ "$device" == *":"* ]]; then
        # Para dispositivo montado por NFS
        local mount_point="/mnt/nfs_source"
        md5sum "$mount_point"
    else
        md5sum "$device"
    fi
}

# Função para validar dispositivo local
validate_local_device() {
    if [ ! -e "$1" ]; then
        echo "Erro: O dispositivo $1 não existe!"
        exit 1
    fi
}

# Função para configurar o servidor NFS (normalmente não necessário se o servidor já estiver configurado)
setup_nfs_server() {
    local nfs_server=$1
    local nfs_path=$2

    # Cria o diretório de exportação se ele não existir
    ssh "root@$nfs_server" "mkdir -p $nfs_path"

    # Adiciona a configuração de exportação se ainda não estiver presente
    ssh "root@$nfs_server" "grep -q '^$nfs_path' /etc/exports || echo '$nfs_path *(rw,sync,no_root_squash)' >> /etc/exports"

    # Reinicia o servidor NFS
    ssh "root@$nfs_server" "exportfs -a && systemctl restart nfs-kernel-server"

    echo "Servidor NFS configurado com sucesso"
}


# Função para listar discos disponíveis
list_disks() {
    local nfs_server=$1
    echo "Discos disponíveis na máquina remota:"
    echo "--------------------------------"
    ssh "root@$nfs_server" "lsblk -d -o NAME,SIZE,MODEL | grep -v 'loop'"
    echo "--------------------------------"
}

# Função para validar e montar o compartilhamento NFS com tratamento de erros aprimorado
validate_nfs_share() {
    local nfs_server=$1
    local nfs_path=$2
    local mount_point="/mnt/nfs_source"

    # Cria o ponto de montagem se ele não existir
    if [ ! -d "$mount_point" ]; then
        mkdir -p "$mount_point"
    fi

    # Testa a disponibilidade do servidor NFS
    if ! ping -c 3 "$nfs_server" &> /dev/null; then  # Aumentou as tentativas de ping para maior confiabilidade
        echo "Erro: Não foi possível alcançar o servidor NFS $nfs_server. Verifique a conectividade de rede e o firewall."
        exit 1
    fi

    # Tenta montar o compartilhamento NFS com saída detalhada para depuração
    if ! mount -t nfs -v "$nfs_server:$nfs_path" "$mount_point" 2>&1 | tee /tmp/nfs_mount.log; then
        echo "Erro: Não foi possível montar o compartilhamento NFS de $nfs_server:$nfs_path. Verifique a configuração do servidor NFS e as exportações."
        echo "Detalhes registrados em /tmp/nfs_mount.log" # Log para análise detalhada
        exit 1
    fi

    echo "Compartilhamento NFS montado com sucesso em $mount_point"
}

# Função para limpar a montagem NFS
cleanup_nfs() {
    local mount_point="/mnt/nfs_source"
    if mountpoint -q "$mount_point"; then
        umount "$mount_point"
    fi
}

# Limpa a tela
clear

# Mensagem de boas-vindas
echo "=== Ferramenta de Clonagem de VM ==="
echo "Esta ferramenta ajudará você a clonar/espelhar sua máquina virtual"
echo "----------------------------------------"

# Escolha o método de clonagem
echo "Selecione o método de clonagem:"
echo "1. Dispositivos locais"
echo "2. Remoto via NFS"
read -p "Digite sua escolha (1/2): " CLONE_METHOD


case $CLONE_METHOD in
    1)
        # Clonagem local
        echo "Discos locais disponíveis:"
        echo "--------------------------------"
        lsblk -d -o NAME,SIZE,MODEL | grep -v 'loop'
        echo "--------------------------------"

        read -p "Digite o dispositivo de origem (por exemplo, /dev/sda): " SOURCE_DEVICE
        validate_local_device "$SOURCE_DEVICE"

        read -p "Digite o dispositivo de destino (por exemplo, /dev/sdb): " DEST_DEVICE
        validate_local_device "$DEST_DEVICE"

        # Confirma a operação
        echo "AVISO: Isso APAGARÁ TODOS OS DADOS em $DEST_DEVICE!"
        read -p "Tem certeza de que deseja continuar? (sim/não): " CONFIRM

        if [ "$CONFIRM" != "sim" ]; then
            echo "Operação cancelada pelo usuário"
            exit 0
        fi

        # Calcula o hash de origem antes de copiar
        echo "Calculando o hash de origem..."
        SOURCE_HASH=$(calculate_hash "$SOURCE_DEVICE")
        echo "Hash de origem: $SOURCE_HASH"

        # Executa o processo de clonagem local
        echo "Iniciando o processo de clonagem local..."
        dd if="$SOURCE_DEVICE" of="$DEST_DEVICE" bs=4M status=progress conv=noerror,sync
        ;;

    2)
        # Clonagem remota via NFS
        read -p "Digite o IP do servidor NFS: " NFS_SERVER
        NFS_PATH="/exports/vm"  # Ou leia NFS_PATH se necessário

        # Valida e monta o compartilhamento NFS PRIMEIRO
        validate_nfs_share "$NFS_SERVER" "$NFS_PATH"

        # Lista os discos disponíveis na máquina remota (após a conexão NFS)
        list_disks "$NFS_SERVER"

        read -p "Digite o dispositivo de origem da lista acima (por exemplo, sda): " REMOTE_DEVICE
        REMOTE_DEVICE="/dev/$REMOTE_DEVICE"


        echo "Discos locais disponíveis para destino:"
        echo "--------------------------------"
        lsblk -d -o NAME,SIZE,MODEL | grep -v 'loop'
        echo "--------------------------------"
        read -p "Digite o dispositivo de destino (por exemplo, /dev/sdb): " DEST_DEVICE

        validate_local_device "$DEST_DEVICE"

        # Define o caminho do dispositivo de origem
        SOURCE_DEVICE="/mnt/nfs_source/$REMOTE_DEVICE"

        # Confirma a operação
        echo "AVISO: Isso APAGARÁ TODOS OS DADOS em $DEST_DEVICE!"
        echo "Origem: $SOURCE_DEVICE (via NFS)"
        echo "Destino: $DEST_DEVICE"
        read -p "Tem certeza de que deseja continuar? (sim/não): " CONFIRM

        if [ "$CONFIRM" != "sim" ]; then
            echo "Operação cancelada pelo usuário"
            cleanup_nfs # Limpa a montagem NFS em caso de cancelamento
            exit 0
        fi

        # Calcula o hash de origem antes de copiar
        echo "Calculando o hash de origem..."
        SOURCE_HASH=$(calculate_hash "$SOURCE_DEVICE")
        echo "Hash de origem: $SOURCE_HASH"

        # Executa o processo de clonagem remota
        echo "Iniciando o processo de clonagem remota..."
        dd if="$SOURCE_DEVICE" of="$DEST_DEVICE" bs=4M status=progress conv=noerror,sync

        # Limpa a montagem NFS após a clonagem
        cleanup_nfs
        ;;

    *)
        echo "Escolha inválida!"
        exit 1
        ;;
esac

# Calcula o hash de destino após a cópia
echo "Calculando o hash de destino..."
DEST_HASH=$(calculate_hash "$DEST_DEVICE")
echo "Hash de destino: $DEST_HASH"

# Compara os hashes
if [ "$SOURCE_HASH" = "$DEST_HASH" ]; then
    echo "Verificação de hash bem-sucedida! Clonagem concluída com sucesso."
else
    echo "AVISO: Incompatibilidade de hash! A unidade clonada pode não ser idêntica à origem."
    echo "Hash de origem: $SOURCE_HASH"
    echo "Hash de destino: $DEST_HASH"
fi
