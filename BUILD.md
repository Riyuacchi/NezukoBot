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
The Docker container does not have the required build tools for voice support.
Voice features are disabled by default on Linux to avoid build failures.

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
Le conteneur Docker n'a pas les outils de compilation requis pour le support vocal.
Les fonctionnalités vocales sont désactivées par défaut sur Linux pour éviter les erreurs de compilation.
