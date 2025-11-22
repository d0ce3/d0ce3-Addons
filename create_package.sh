#!/bin/bash

echo "📦 Creando paquete MegaCMD..."

# Leer versión de links.json
VERSION=$(grep -oP '"version":\s*"\K[^"]+' data/links.json | head -1)

echo "📌 Versión: $VERSION"

# Crear directorio temporal
rm -rf /tmp/megacmd_package
mkdir -p /tmp/megacmd_package/modules

# Copiar archivos
echo "📋 Copiando archivos..."
cp megacmd/MegaCmd.addon /tmp/megacmd_package/
cp megacmd/megacmd_tool.py /tmp/megacmd_package/
cp megacmd/modules/*.py /tmp/megacmd_package/modules/

# Crear ZIP
echo "🗜️ Comprimiendo..."
cd /tmp/megacmd_package
zip -r -q megacmd_${VERSION}.zip .
cd - > /dev/null

# Mover a destino
mv /tmp/megacmd_package/megacmd_${VERSION}.zip megacmd/

# Limpiar
rm -rf /tmp/megacmd_package

echo "✅ Paquete creado: megacmd/megacmd_${VERSION}.zip"
echo ""
echo "📤 Ahora ejecutá:"
echo git add .
echo git commit -m "fix"
echo git push
