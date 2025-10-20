# Build Instructions / Instructions de compilation

## English

### Building without Voice Support (Default)
```bash
cargo build --release
```

### Building with Voice Support (Windows)

**Prerequisites:**
- Visual Studio Build Tools 2022 with C++ support
- CMake (usually included with VS Build Tools)

**Build command:**
```bash
cargo build --release --features voice
```

**Run command:**
```bash
cargo run --release --features voice
```

### Linux Server (Pelican Panel)

**To enable voice support on Pelican Panel:**

1. SSH into your server or use the Pelican Panel console
2. Navigate to your bot directory: `cd /home/container`
3. Run the dependency installer (requires root/sudo):
   ```bash
   chmod +x install-deps.sh
   sudo ./install-deps.sh
   ```

   **OR manually install:**
   ```bash
   # For Debian/Ubuntu
   sudo apt-get update
   sudo apt-get install -y cmake build-essential libopus-dev pkg-config

   # For Alpine Linux
   sudo apk add cmake make gcc g++ musl-dev opus-dev pkgconfig
   ```

4. Build with voice support:
   ```bash
   cargo build --release --features voice
   ```

**Note:** If you don't have sudo access, contact your hosting provider to install these packages in the Docker image.

---

## Français

### Compilation sans support vocal (Par défaut)
```bash
cargo build --release
```

### Compilation avec support vocal (Windows)

**Prérequis:**
- Visual Studio Build Tools 2022 avec support C++
- CMake (généralement inclus avec VS Build Tools)

**Commande de compilation:**
```bash
cargo build --release --features voice
```

**Commande d'exécution:**
```bash
cargo run --release --features voice
```

### Serveur Linux (Pelican Panel)

**Pour activer le support vocal sur Pelican Panel:**

1. Connectez-vous en SSH à votre serveur ou utilisez la console Pelican Panel
2. Naviguez vers le répertoire du bot: `cd /home/container`
3. Exécutez l'installateur de dépendances (nécessite root/sudo):
   ```bash
   chmod +x install-deps.sh
   sudo ./install-deps.sh
   ```

   **OU installez manuellement:**
   ```bash
   # Pour Debian/Ubuntu
   sudo apt-get update
   sudo apt-get install -y cmake build-essential libopus-dev pkg-config

   # Pour Alpine Linux
   sudo apk add cmake make gcc g++ musl-dev opus-dev pkgconfig
   ```

4. Compilez avec le support vocal:
   ```bash
   cargo build --release --features voice
   ```

**Note:** Si vous n'avez pas accès sudo, contactez votre hébergeur pour installer ces packages dans l'image Docker.

**Solution automatique recommandée - Modifier la commande de démarrage:**

Dans Pelican Panel, allez dans "Startup" et modifiez la commande de démarrage pour:
```bash
chmod +x pelican-start.sh && ./pelican-start.sh
```

Ce script va:
- Mettre à jour automatiquement depuis git (si AUTO_UPDATE=1)
- Tenter d'installer les dépendances automatiquement
- Compiler avec voice support si les outils sont disponibles
- Compiler sans voice support sinon (pour éviter les erreurs)

**Pour forcer l'installation des dépendances:**
Si le script automatique échoue, vous devez installer les dépendances manuellement via SSH:
```bash
# Connectez-vous en SSH au serveur
cd /home/container
sudo apt-get update && sudo apt-get install -y cmake build-essential libopus-dev pkg-config
```

Ensuite redémarrez le serveur dans Pelican Panel.
