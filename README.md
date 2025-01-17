# OS Cloning Script with NFS Support

Este script permite clonar/espelhar um sistema operacional de um dispositivo para outro, seja localmente ou através de NFS, usando o comando `dd` e verifica a integridade dos dados usando hash MD5.

## Requisitos

- Sistema operacional Linux
- Acesso root (sudo) em ambas as máquinas
- Para clonagem local:
  - Dispositivos de origem e destino conectados ao sistema
- Para clonagem via NFS:
  - Máquinas em modo bridge na mesma rede
  - Servidor NFS configurado na máquina remota
  - Cliente NFS instalado na máquina local
  - Permissões adequadas no compartilhamento NFS

## ⚠️ Avisos Importantes

1. **FAÇA BACKUP DOS SEUS DADOS!** Este script sobrescreverá TODOS os dados no dispositivo de destino.
2. Execute o script quando os sistemas não estiverem em uso ativo.
3. NÃO execute em partições montadas ou no sistema operacional em execução.
4. Certifique-se de identificar corretamente os dispositivos para evitar perda de dados.

## Instalação

1. Baixe o script:
   ```bash
   wget https://raw.githubusercontent.com/seu-usuario/seu-repo/main/clone_os.sh
   ```

2. Torne o script executável:
   ```bash
   chmod +x clone_os.sh
   ```

## Como Usar

### Preparação

1. Identifique seus dispositivos:
   ```bash
   sudo fdisk -l
   ```
   Este comando listará todos os dispositivos conectados. Anote os caminhos (ex: /dev/sda, /dev/sdb)

2. Execute o script como root:
   ```bash
   sudo ./clone_os.sh
   ```

### Modos de Operação

O script oferece dois modos de operação:

1. **Clonagem Local**
   - Para clonar entre dispositivos na mesma máquina
   - Selecione opção 1 quando solicitado
   - Digite o dispositivo de origem (ex: /dev/sda)
   - Digite o dispositivo de destino (ex: /dev/sdb)

2. **Clonagem via NFS**
   - Para clonar de uma máquina remota usando NFS
   - Selecione opção 2 quando solicitado
   - Digite o IP do servidor NFS
   - Digite o caminho do compartilhamento NFS
   - Digite o dispositivo na máquina remota (ex: /dev/sda)
   - Digite o dispositivo de destino local (ex: /dev/sdb)

### Exemplo de Uso Local

```bash
=== VM Cloning Tool ===
This tool will help you clone/mirror your virtual machine
----------------------------------------
Select cloning method:
1. Local devices
2. Remote via NFS
Enter your choice (1/2): 1
Enter source device (e.g., /dev/sda): /dev/sda
Enter destination device (e.g., /dev/sdb): /dev/sdb
```

### Exemplo de Uso NFS

```bash
=== VM Cloning Tool ===
This tool will help you clone/mirror your virtual machine
----------------------------------------
Select cloning method:
1. Local devices
2. Remote via NFS
Enter your choice (1/2): 2
Enter NFS server IP: 192.168.1.100
Enter NFS share path (e.g., /exports/vm): /exports/vm
Enter source device on NFS share (e.g., /dev/sda): /dev/sda
Enter destination device (e.g., /dev/sdb): /dev/sdb
```

## Configuração NFS

### No Servidor (Máquina Remota)

1. Instale o servidor NFS:
   ```bash
   sudo apt-get install nfs-kernel-server   # Para Debian/Ubuntu
   sudo yum install nfs-utils              # Para RHEL/CentOS
   ```

2. Configure o compartilhamento NFS em `/etc/exports`:
   ```bash
   sudo nano /etc/exports
   ```
   Adicione a linha:
   ```
   /exports/vm    192.168.1.0/24(rw,sync,no_root_squash)
   ```

3. Crie o diretório de compartilhamento e aplique as configurações:
   ```bash
   sudo mkdir -p /exports/vm
   sudo exportfs -a
   sudo systemctl restart nfs-kernel-server
   ```

### No Cliente (Máquina Local)

1. Instale o cliente NFS:
   ```bash
   sudo apt-get install nfs-common   # Para Debian/Ubuntu
   sudo yum install nfs-utils       # Para RHEL/CentOS
   ```

## Funcionalidades

1. **Validação de Entrada**
   - Verifica se os dispositivos existem
   - Testa conexão com servidor NFS
   - Valida montagem do compartilhamento NFS
   - Solicita confirmação antes de prosseguir

2. **Clonagem com DD**
   - Utiliza o comando dd para cópia bit a bit
   - Block size de 4MB para melhor performance
   - Mostra progresso durante a cópia
   - Suporta clonagem local e remota via NFS

3. **Verificação de Integridade**
   - Calcula hash MD5 do dispositivo fonte
   - Calcula hash MD5 do dispositivo destino
   - Compara os hashes para garantir a integridade

## Parâmetros do DD

O script usa os seguintes parâmetros do dd:
- `bs=4M`: Define o tamanho do bloco em 4MB
- `status=progress`: Mostra o progresso da cópia
- `conv=noerror,sync`: Continua em caso de erros e mantém sincronização

## Resolução de Problemas

1. **"Device does not exist"**
   - Verifique se digitou o caminho correto do dispositivo
   - Use `sudo fdisk -l` para listar dispositivos disponíveis

2. **"Cannot reach NFS server"**
   - Verifique se o IP do servidor está correto
   - Confirme se as máquinas estão na mesma rede
   - Teste a conectividade com ping

3. **"Cannot mount NFS share"**
   - Verifique se o servidor NFS está rodando
   - Confirme as permissões no /etc/exports
   - Verifique as configurações de firewall

4. **Hash não corresponde**
   - Verifique se há setores defeituosos
   - Tente executar o processo novamente
   - Verifique se os dispositivos não foram modificados durante a cópia

## Limitações

- O dispositivo de destino deve ter capacidade igual ou maior que o fonte
- O processo pode ser demorado dependendo do tamanho dos dispositivos
- Requer configuração adequada do NFS
- Não é possível clonar sistemas em execução

## Segurança

- Sempre verifique duas vezes os dispositivos antes de confirmar
- Configure corretamente as permissões do NFS
- Use restrições de IP no /etc/exports
- Faça backup de dados importantes antes de usar

## Suporte

Para problemas ou sugestões, abra uma issue no repositório do projeto.