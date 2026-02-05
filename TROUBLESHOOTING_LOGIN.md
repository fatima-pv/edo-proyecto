# 🔧 Solución: Login Fallando (401)

## Problema
Los usuarios no se crearon en DynamoDB porque las credenciales de AWS expiraron.

## Solución

### 1. Renovar Credenciales de AWS Academy

Ve a tu **AWS Academy Lab** y obtén nuevas credenciales:
- Click en "AWS Details"
- Click en "Show" para ver CLI credentials
- Copia las 3 líneas

### 2. Configurar Credenciales

```bash
mkdir -p ~/.aws
```

Crear `~/.aws/credentials`:
```bash
nano ~/.aws/credentials
```

Pegar (CON TUS VALORES REALES):
```
[default]
aws_access_key_id=ASIA...
aws_secret_access_key=...
aws_session_token=...
```

Guardar: `Ctrl+X`, `Y`, `Enter`

Crear `~/.aws/config`:
```bash
nano ~/.aws/config
```

Pegar:
```
[default]
region=us-east-1
output=json
```

Guardar: `Ctrl+X`, `Y`, `Enter`

### 3. Crear Usuarios en DynamoDB

```bash
cd /Users/mauricioalarcon/utec/cloud/edo-proyecto
./scripts/seed-data.sh dev
```

Deberías ver:
```
✅ Cliente creado: cliente@test.com / cliente123
✅ Chef creado: chef@edosushi.com / chef123
✅ Empaquetador creado: empaquetador@edosushi.com / emp123
✅ Motorizado creado: delivery@edosushi.com / delivery123
```

### 4. Probar Login

Recarga la página del frontend y haz login con:
- **Email:** `cliente@test.com`
- **Password:** `cliente123`

¡Debería funcionar! ✅
