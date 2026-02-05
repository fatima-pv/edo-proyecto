#!/bin/bash

# Detener el script si hay errores
set -e

deploy_service() {
    service_path=$1
    service_name=$(basename $service_path)
    
    echo "--------------------------------------------------"
    echo "🚀 Desplegando $service_name..."
    echo "--------------------------------------------------"
    
    cd $service_path
    
    # 1. Asegurar que existe package.json
    if [ ! -f package.json ]; then
        echo "⚠️  No se encontró package.json. Creándolo..."
        npm init -y
    fi

    # 2. Instalar dependencias (incluyendo plugins)
    echo "📦 Instalando dependencias..."
    npm install
    
    # Caso especial: workflow-service necesita este plugin sí o sí
    if [ "$service_name" == "workflow-service" ]; then
        npm install serverless-step-functions --save-dev
    fi

    # 3. Desplegar
    echo "☁️  Ejecutando Serverless Deploy..."
    npx serverless@3 deploy
    
    # Volver a la raíz
    cd - > /dev/null
    echo "✅ $service_name desplegado correctamente."
    echo ""
}

# Desplegar los 3 servicios
deploy_service "backend/auth-service"
deploy_service "backend/order-service"
deploy_service "backend/workflow-service"

echo "🎉 ¡Todo desplegado con éxito!"
