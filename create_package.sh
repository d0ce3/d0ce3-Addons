#!/bin/bash

echo "📦 Creando paquete de d0ce3..."

VERSION=$(grep -oP '"version":\s*"\K[^"]+' data/links.json | head -1)

echo "📌 Versión: $VERSION"

rm -rf /tmp/megacmd_package
mkdir -p /tmp/megacmd_package/modules
mkdir -p /tmp/megacmd_package/core

# Copiar archivos
echo "📋 Copiando archivos..."

cp megacmd/d0ce3tools.addon /tmp/megacmd_package/
cp megacmd/d0ce3_tools.py /tmp/megacmd_package/
cp megacmd/modules/*.py /tmp/megacmd_package/modules/
cp megacmd/core/*.py /tmp/megacmd_package/core/

echo "🗜️ Comprimiendo..."

cd /tmp/megacmd_package
zip -r -q d0ce3tools_${VERSION}.zip .
cd - > /dev/null

mv /tmp/megacmd_package/d0ce3tools_${VERSION}.zip megacmd/

rm -rf /tmp/megacmd_package

echo "✅ Paquete creado: megacmd/d0ce3tools_${VERSION}.zip"
echo ""
echo "📤 Ahora ejecutá:"
echo git add .
echo git commit -m 'fix'
echo git push
