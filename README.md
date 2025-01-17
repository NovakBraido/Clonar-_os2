# OS Cloning Script with SSH Support

Este script permite clonar/espelhar um sistema operacional de um dispositivo para outro, seja localmente ou através de SSH, usando o comando `dd` e verifica a integridade dos dados usando hash MD5.

## Requisitos

- Sistema operacional Linux
- Acesso root (sudo) em ambas as máquinas
- Para clonagem local:
  - Dispositivos de origem e destino conectados ao sistema
- Para clonagem via SSH:
  - Acesso SSH configurado na máquina remota
  - Chaves SSH configuradas (recomendado)
  - Permissões sudo na máquina remota

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

2. **Clonagem via SSH**
   - Para clonar de uma máquina remota
   - Selecione opção 2 quando solicitado
   - Digite o host SSH (ex: usuario@servidor-remoto)
   - Digite o dispositivo na máquina remota (ex: /dev/sda)
   - Digite o dispositivo de destino local (ex: /dev/sdb)

### Exemplo de Uso Local

```bash
=== VM Cloning Tool ===
This tool will help you clone/mirror your virtual machine
----------------------------------------
Select cloning method:
1. Local devices
2. Remote via SSH
Enter your choice (1/2): 1
Enter source device (e.g., /dev/sda): /dev/sda
Enter destination device (e.g., /dev/sdb): /dev/sdb
```

### Exemplo de Uso SSH

```bash
=== VM Cloning Tool ===
This tool will help you clone/mirror your virtual machine
----------------------------------------
Select cloning method:
1. Local devices
2. Remote via SSH
Enter your choice (1/2): 2
Enter source SSH host (e.g., user@remote-host): user@192.168.1.100
Enter source device on remote host (e.g., /dev/sda): /dev/sda
Enter destination device (e.g., /dev/sdb): /dev/sdb
```

## Configuração SSH

Para usar a clonagem via SSH:

1. Configure o acesso SSH na máquina remota:
   ```bash
   ssh-keygen
   ssh-copy-id usuario@servidor-remoto
   ```

2. Configure sudo sem senha para o comando dd na máquina remota:
   ```bash
   sudo visudo
   ```
   Adicione a linha:
   ```
   usuario ALL=(ALL) NOPASSWD: /bin/dd
   ```

## Funcionalidades

1. **Validação de Entrada**
   - Verifica se os dispositivos existem
   - Testa conexão SSH e acesso aos dispositivos remotos
   - Solicita confirmação antes de prosseguir

2. **Clonagem com DD**
   - Utiliza o comando dd para cópia bit a bit
   - Block size de 4MB para melhor performance
   - Mostra progresso durante a cópia
   - Suporta clonagem local e remota via SSH

3. **Verificação de Integridade**
   - Calcula hash MD5 do dispositivo fonte (local ou remoto)
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

2. **"Cannot connect to SSH host"**
   - Verifique se o host SSH está correto
   - Confirme se as chaves SSH estão configuradas
   - Teste a conexão SSH manualmente

3. **"Permission denied"**
   - Verifique se sudo está configurado corretamente
   - Configure sudo sem senha para dd na máquina remota

4. **Hash não corresponde**
   - Verifique se há setores defeituosos
   - Tente executar o processo novamente
   - Verifique se os dispositivos não foram modificados durante a cópia

## Limitações

- O dispositivo de destino deve ter capacidade igual ou maior que o fonte
- O processo pode ser demorado dependendo do tamanho dos dispositivos
- Requer configuração adequada de SSH e sudo
- Não é possível clonar sistemas em execução

## Segurança

- Sempre verifique duas vezes os dispositivos antes de confirmar
- Use conexões SSH seguras (preferencialmente com chaves)
- Configure adequadamente as permissões sudo
- Faça backup de dados importantes antes de usar

## Suporte

Para problemas ou sugestões, abra uma issue no repositório do projeto.