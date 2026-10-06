# Gchess: datos persistentes y recuperación

## Estado operativo después de la migración (6 de octubre de 2026)

- Se contrató gchess-db (PostgreSQL 18, Virginia, 1 GB, US$6.30/mes adicionales).
- El export de la instancia anterior se descargó por SSH a una carpeta privada
  local y se verificó su formato y SHA-256. Contenía 14 registros; no había
  cuentas ni partidas. La instancia local del Escritorio se respaldó por separado.
- Se aplicaron las migraciones en PostgreSQL y se importó un export actualizado;
  los conteos por modelo coincidieron. Gchess quedó conectado por DATABASE_URL
  interna con sslmode=require. Las credenciales no se incluyen en este documento.
- Render completó el deploy de configuración. Se verificaron PostgreSQL, TLS y
  migraciones desde la aplicación. Un registro temporal de sesión sobrevivió a
  un reinicio controlado y luego se retiró.
- El código de diagnóstico/health/export/restore sigue modificado localmente;
  esta migración usó la versión ya publicada, que soportaba DATABASE_URL.
- Se solicitó un export lógico nativo de PostgreSQL en Render. Verificar su
  disponibilidad en Recovery. La recuperación a un punto en el tiempo muestra
  una ventana de 3 días para este workspace y requiere inicialización previa.
- Pendiente: publicar las herramientas locales, configurar /healthz/ después
  de publicarlas, programar exports independientes y probar una restauración
  completa del backup PostgreSQL en una instancia separada.

## Estado observado antes de la migración (6 de octubre de 2026)

El servicio Gchess en Render no tenía DATABASE_URL. El código usa /app/db.sqlite3
si no está configurada. Docker excluye db.sqlite3 de la imagen: un deploy puede
crear una base vacía. El código nuevo añade diagnósticos, pero NO conecta ni crea
una base por sí solo y NO migra los datos actuales automáticamente.

Propuesta preparada, sin contratar: PostgreSQL 18, Virginia, 0.1 CPU / 256 MB,
1 GB, autoscaling desactivado. El dashboard mostraba US$6.30/mes adicionales
(US$6 compute + US$0.30 almacenamiento). Confirmar el total antes de crear.

## Orden para preservar los datos del servicio actual

1. Antes de hacer push/deploy/restart o cambiar DATABASE_URL, acordar una ventana
   sin partidas activas, registros ni cambios de usuarios. Bloquear tráfico de
   escritura durante la exportación y hasta validar la nueva base.
2. Desde Shell/SSH del servicio ACTUAL, exportar con el Django que ya está publicado:

   ```bash
   python manage.py dumpdata --all --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude sessions --exclude admin.logentry --output /tmp/gchess-live.json
   ```

   Ese archivo contiene datos personales y contraseñas hasheadas. No pegarlo en
   el chat, GitHub o logs. Descargarlo por SSH/SCP a un equipo privado antes de
   cualquier reinicio. Los archivos en /tmp tampoco sobreviven a un deploy.
   Registrar además conteos por modelo y comparar tras la importación.
   La base local del Escritorio NO equivale a la de Render.
3. Crear PostgreSQL solo después de aprobar el costo, en Virginia. Utilizar la
   Internal Database URL para DATABASE_URL; no mostrarla ni ponerla en Git.
   Restringir acceso externo según la vía elegida para migrar y administrar.
4. En una base PostgreSQL nueva sin usuarios, ejecutar las migraciones y cargar
   el export del paso 2 con loaddata. El catálogo inicial de logros se genera por
   migraciones: comprobar que sus claves/IDs correspondan a los del export antes
   de cargar; si no coinciden, preparar una importación explícita en lugar de
   borrar datos o forzar relaciones. La herramienta restore_data nueva maneja
   ese catálogo cuando se usa su propio formato export_data.
5. Comparar usuarios, partidas, jugadas, progreso, grupos y relaciones. Probar
   login con una cuenta existente y abrir una partida histórica. Mantener el
   archivo original fuera de Render; no habilitar tráfico si la validación falla.
6. Conectar Gchess a esa base vía DATABASE_URL y publicar los cambios revisados.
   Mantener DJANGO_SECRET_KEY para no invalidar firmas innecesariamente.
7. Ejecutar `python manage.py check_storage` y comprobar `/healthz/`. Configurar
   el Health Check Path de Render a `/healthz/` cuando el endpoint esté publicado.
8. Crear una cuenta/partida de prueba autorizada, hacer un reinicio o deploy
   controlado y verificar que SIGUEN presentes. Ese ensayo es necesario para
   declarar completa la persistencia en producción.

No iniciar un deploy con el fin de instalar las herramientas de exportación
antes de salvar la base SQLite de la instancia actual: eso puede perderla.

## Exportación portable con el código nuevo

```bash
python manage.py export_data --output backups/gchess-2026-10-06.json.gz
```

Genera un archivo comprimido y un `.manifest.json` con SHA-256 y conteos por
modelo. No sobrescribe archivos existentes. En PostgreSQL lee una instantánea
consistente con REPEATABLE READ. No exporta sesiones, permisos generados,
content types ni el log de administración; las sesiones deben volver a iniciarse.
Los permisos y grupos de usuario usan claves naturales. El export no incluye
archivos subidos ni secretos de configuración: respaldarlos por separado.

Copiar AMBOS archivos a almacenamiento privado fuera del servicio. Una copia
en el mismo contenedor no es un backup persistente. Están excluidos de Git y
Docker. No se configuró todavía una tarea automática ni almacenamiento externo.

## Ensayo seguro de restauración

Usar una base separada y recién migrada, con el mismo esquema/código:

```bash
python manage.py migrate
python manage.py restore_data backups/gchess-2026-10-06.json.gz
```

restore_data valida hash, versión y conteos, rechaza bases con datos de usuarios
y revierte la importación si falla. Permite únicamente el catálogo de logros
que las migraciones crean por defecto y lo reemplaza dentro de la transacción.
No es una herramienta para fusionar dos bases ni sobrescribir producción.
Verificar después login, permisos, historial y estadísticas. El manifiesto es
un control de integridad, no una firma: solo cargar exports de origen confiable.

## Recuperación operativa

Render Postgres pago incluye recuperación a un punto en el tiempo y exports.
Confirmar la ventana de retención del plan contratado y probar recuperación a
una instancia separada. Mantener exports independientes fuera del proveedor.
Propuesta inicial de operación: export diario externo, conservar 7 diarios y
4 semanales, y un ensayo mensual de restauración. Esto es una política propuesta,
NO una automatización activa. Medir cuánto tiempo se tarda en restaurar.

Documentación:
- https://render.com/docs/postgresql-creating-connecting
- https://render.com/docs/postgresql-backups
- https://render.com/docs/disks

## Controles añadidos

- `manage.py check` avisa si Render sigue usando SQLite.
- `manage.py check --deploy --tag database` exige PostgreSQL.
- `manage.py check_storage` verifica conexión y migraciones sin revelar credenciales.
- `/healthz/` ejecuta SELECT 1, devuelve 200/503 sin errores internos ni credenciales.
  No incrementa visitas ni crea sesiones. No consulta Gemini/Stockfish.
- PostgreSQL usa connect_timeout=5 y conexiones no persistentes para ASGI.
- Las URLs con contraseñas escapadas se interpretan correctamente.

Estado de producción verificado el 2026-10-06:
- Gchess conectado a gchess-db PostgreSQL con TLS y migraciones aplicadas.
- Transferencia comparada: 14 registros; no había usuarios ni partidas.
- Sesión de prueba conservada después de reiniciar el servicio y retirada al terminar.
- Export nativo de Render completado y descargado; respaldo previo exportado por separado.
- Clave SSH temporal revocada y credenciales temporales locales retiradas.
- Plan contratado: US$6/mes + 1 GB US$0,30/mes; almacenamiento automático desactivado.

Pendiente: ensayo de restauración PostgreSQL en una instancia aislada y automatización
 de copias externas. Las herramientas y /healthz/ descritas arriba están preparadas
localmente y todavía no se publicaron. Los ensayos locales usan SQLite aislado.