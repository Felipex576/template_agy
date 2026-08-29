#!/usr/bin/env bash
# ==============================================================================
# Synapse & Data Pipeline Installer (Bash / Linux / macOS)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-$(pwd)}"

echo -e "\033[36m=================================================================\033[0m"
echo -e "\033[33m    Synapse Protocol & Data Pipeline Architecture Installer     \033[0m"
echo -e "\033[36m=================================================================\033[0m"

install_agent_layer() {
    local dest="$1"
    echo -e "\n\033[36m[*] Installing AI Agent Layer (.agents, .synapse, adapters)...\033[0m"
    
    local src_agents="$SCRIPT_DIR/.agents"
    local src_synapse="$SCRIPT_DIR/.synapse"
    local src_gemini="$SCRIPT_DIR/.gemini"

    # If local source does not exist (remote one-liner execution), download from GitHub
    if [ ! -d "$src_agents" ]; then
        echo -e "\033[36m  [*] Remote execution detected. Downloading template archive from GitHub...\033[0m"
        local temp_dir=$(mktemp -d)
        curl -fsSL https://github.com/Felipex576/template_agy/archive/refs/heads/main.tar.gz | tar -xz -C "$temp_dir"
        src_agents="$temp_dir/template_agy-main/.agents"
        src_synapse="$temp_dir/template_agy-main/.synapse"
        src_gemini="$temp_dir/template_agy-main/.gemini"
    fi

    if [ -d "$src_agents" ]; then
        cp -r "$src_agents" "$dest/"
        echo -e "\033[32m  [+] Copied .agents/ (Skills, Subagents, AGENTS.md)\033[0m"
    fi

    if [ -d "$src_synapse" ]; then
        cp -r "$src_synapse" "$dest/"
        echo -e "\033[32m  [+] Copied .synapse/ (Persistent Memory, SDD Protocol)\033[0m"
    fi

    if [ -d "$src_gemini" ]; then
        cp -r "$src_gemini" "$dest/"
        echo -e "\033[32m  [+] Copied .gemini/ (GEMINI.md)\033[0m"
    fi

    cat << 'EOF' > "$dest/CLAUDE.md"
# Master Data Pipeline Architecture & Guidelines
Please strictly follow the master engineering guidelines in `.agents/AGENTS.md` and the memory/SDD lifecycle in `.synapse/PROTOCOL.md`.
EOF
    echo -e "\033[32m  [+] Generated CLAUDE.md adapter\033[0m"

    if [ -n "$temp_dir" ] && [ -d "$temp_dir" ]; then
        rm -rf "$temp_dir"
    fi
}

scaffold_new_project() {
    local dest="$1"
    local project_name="$2"
    local kebab_project="${project_name//_/-}"

    echo -e "\n\033[36m[*] Scaffolding full 6-layer architecture for project '$project_name'...\033[0m"

    mkdir -p "$dest/src/config" "$dest/src/jobs" "$dest/src/queries" "$dest/src/resources" \
             "$dest/src/transformations" "$dest/src/utils/extra_files" \
             "$dest/tests/config" "$dest/tests/jobs" "$dest/tests/queries" "$dest/tests/resources" \
             "$dest/tests/transformations" "$dest/serverless-files/analytics/resources"

    touch "$dest/src/__init__.py" "$dest/tests/__init__.py"
    echo -e "\033[32m  [+] Created standard folder hierarchy\033[0m"
}

read -p "¿Es este un proyecto nuevo? (s/n): " is_new

if [[ "$is_new" =~ ^[sSyY]$ ]]; then
    read -p "Ingresa el nombre del proyecto/job en snake_case (ej: control_caja): " project_name
    project_name="${project_name:-data_pipeline}"

    scaffold_new_project "$TARGET_DIR" "$project_name"
    install_agent_layer "$TARGET_DIR"

    echo -e "\n\033[32m=================================================================\033[0m"
    echo -e "\033[33m  ¡Proyecto '$project_name' creado e inicializado con éxito!      \033[0m"
    echo -e "\033[32m=================================================================\033[0m"
else
    read -p "¿Deseas instalar las skills, subagentes y memoria persistente en este proyecto? (s/n): " install_agents
    if [[ "$install_agents" =~ ^[sSyY]$ ]]; then
        install_agent_layer "$TARGET_DIR"
        echo -e "\n\033[32m=================================================================\033[0m"
        echo -e "\033[33m  ¡Capa de IA instalada exitosamente en .agents/ y .synapse/!    \033[0m"
        echo -e "\033[32m=================================================================\033[0m"
    else
        echo -e "\n\033[33mOperación cancelada. No se realizaron cambios.\033[0m"
    fi
fi
