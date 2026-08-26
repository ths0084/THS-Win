# Instalador Automático de Softwares - Requisitos

## Instalação das Dependências

Execute o seguinte comando no terminal para instalar as bibliotecas necessárias:

```bash
pip install customtkinter pyinstaller
```

## Como Executar o Programa

### Modo Desenvolvimento (Python)
```bash
python installer.py
```
*Nota: O programa solicitará automaticamente privilégios de administrador via UAC.*

### Criar Executável (.exe)

Para gerar um arquivo executável único que possa ser distribuído:

```bash
pyinstaller --onefile --windowed --name "InstaladorSoftwares" --icon=NONE installer.py
```

Após a compilação, o executável estará localizado na pasta `dist/`.

## Estrutura do Projeto

- `installer.py`: Código principal da aplicação
- `requirements.txt`: Lista de dependências Python
- `dist/`: Pasta onde o executável será gerado
- `build/`: Arquivos temporários de compilação (pode ser excluído após gerar o .exe)

## Funcionalidades

1. **Interface Gráfica Moderna**: Utiliza CustomTkinter com botões arredondados e tema responsivo
2. **Seleção Personalizada**: Checkboxes para escolher quais softwares instalar
3. **Botões de Atalho**: "Selecionar Tudo" e "Desmarcar Tudo"
4. **Verificação Automática**: Ignora softwares já instalados
5. **Instalação Silenciosa**: Usa flags `/silent` para não interromper o usuário
6. **Elevação UAC**: Solicita permissão de administrador automaticamente
7. **Categorias Visuais**: Separação clara entre softwares Gratuitos (verde) e Comerciais/Trial (vermelho)
8. **Log em Tempo Real**: Mostra o status de cada instalação
9. **Aviso de Reinicialização**: Notifica se algum software exigir reboot

## Softwares Incluídos

A lista completa está no arquivo `installer.py` na variável `SOFTWARE_LIST`, incluindo:
- Navegadores (Chrome, Firefox, Edge, etc.)
- Mídia (VLC, OBS, Spotify, etc.)
- Escritório (LibreOffice, WPS, Adobe Reader, etc.)
- Utilitários (7-Zip, PowerToys, Rufus, etc.)
- Segurança (Avast, Malwarebytes, etc.)
- E muito mais...

## Observações Importantes

1. **WinRAR**: Instalada apenas a versão de teste oficial (trial infinito com avisos)
2. **Softwares Governamentais**: PJE e Assinador Livre podem requerer instalação manual
3. **Winget**: Requer Windows 10/11 atualizado. O script usa o gerenciador nativo do Windows
4. **Antivírus**: Cuidado ao instalar múltiplos antivírus simultaneamente

## Solução de Problemas

### Erro: "winget não foi encontrado"
- Atualize o Windows 10/11
- Instale o App Installer da Microsoft Store

### Erro: "Acesso Negado"
- Execute como Administrador manualmente
- Verifique se o UAC não está bloqueando

### Erro: "customtkinter não encontrado"
- Execute: `pip install customtkinter`
