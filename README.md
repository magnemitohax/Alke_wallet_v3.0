# Alke Wallet — Evaluación Módulo 7 (Desarrollo Web con Django)

Aplicación web para la fintech ficticia Alke Financial que permite gestionar
clientes, cuentas digitales y transacciones, usando Django y su ORM.

## Arquitectura del proyecto

```
alke_wallet/
├── alke_wallet/          # Configuración del proyecto (settings, urls raíz)
├── gestion/               # App principal
│   ├── models.py          # Cliente, Cuenta, Transaccion
│   ├── admin.py            # Registro de modelos en /admin
│   ├── forms.py            # ModelForms + AjusteSaldoForm
│   ├── views.py             # Vistas CRUD + ajuste de saldo + reportes
│   ├── urls.py               # Rutas de la app
│   ├── tests.py               # Pruebas unitarias y de integración
│   ├── migrations/             # Historial de cambios en el esquema
│   └── templates/
│       ├── gestion/              # base.html + templates por modelo
│       └── registration/          # login.html
├── static/css/estilos.css   # Estilos globales
├── docs/screenshots/         # Capturas del proyecto
└── manage.py
```

### Modelo de datos y relaciones

| Modelo        | Relación                        | Detalle |
|---------------|-----------------------------------|---------|
| `Cliente`     | Uno a Uno con `User`               | Login opcional asociado al cliente. |
| `Cuenta`      | Muchos a Uno con `Cliente`         | Un cliente puede tener varias cuentas (`related_name="cuentas"`). |
| `Transaccion` | Muchos a Muchos con `Cuenta`       | Además de la cuenta de origen (FK), puede involucrar otras cuentas relacionadas (`cuentas_relacionadas`), para transferencias. |

## Configuración de la base de datos

- **Motor:** MySQL, configurado en `settings.py`.
- Requiere una base y un usuario creados previamente en el servidor MySQL,
  con los valores reflejados en `DATABASES` (`NAME`, `USER`, `PASSWORD`,
  `HOST`, `PORT`).
- Requiere el driver `mysqlclient` (`pip install mysqlclient`).
- Con MySQL 8.0.x, usar Django 6.0 o inferior (`pip install "django<6.1"`),
  ya que Django 6.1 exige MySQL 8.4 o superior.

## Cómo iniciar el proyecto localmente

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install "django<6.1" mysqlclient

# 3. Crear la base y el usuario en MySQL (una sola vez, desde el cliente mysql)
#    CREATE DATABASE alke_wallet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#    CREATE USER 'alke_user'@'localhost' IDENTIFIED BY 'una_clave_segura';
#    GRANT ALL PRIVILEGES ON alke_wallet.* TO 'alke_user'@'localhost';
#    FLUSH PRIVILEGES;

# 4. Ajustar en alke_wallet/settings.py los valores de DATABASES
#    (NAME, USER, PASSWORD) según lo definido en el paso anterior

# 5. Aplicar migraciones
python manage.py migrate

# 6. Crear un superusuario (para /admin)
python manage.py createsuperuser

# 7. Levantar el servidor
python manage.py runserver
```

Luego abrir `http://127.0.0.1:8000/` (redirige al listado de clientes,
pide login) y `http://127.0.0.1:8000/admin/` para el panel de administración.
El acceso se realiza con el superusuario creado en el paso 5.

## Funcionalidades

- **CRUD completo** (crear, listar, ver detalle, editar, eliminar) para
  `Cliente`, `Cuenta` y `Transaccion`, con vistas basadas en clases
  (`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`).
- **Depósito y extracción de saldo** (`/cuentas/<id>/saldo/`): agrega o
  descuenta un monto del saldo de una cuenta y registra automáticamente la
  transacción correspondiente, dentro de una transacción de base de datos
  atómica. Valida que una extracción no supere el saldo disponible.
- **Transferencia entre cuentas** (`/cuentas/<id>/transferir/`): descuenta
  el monto de la cuenta de origen, lo acredita en la cuenta destino
  seleccionada, y registra la transacción (tipo `TRANSFERENCIA`) vinculando
  ambas cuentas mediante `cuentas_relacionadas`. Todo dentro de una
  transacción de base de datos atómica. Valida que el monto no supere el
  saldo disponible y que la cuenta destino sea distinta de la de origen.
- **Aclaración:** el formulario genérico "Nueva transacción" (CRUD de
  `Transaccion`) solo crea o edita el registro de la transacción; no mueve
  saldo entre cuentas por sí mismo. Los flujos de depósito/extracción y
  transferencia son los que efectivamente actualizan los saldos.
- **Autenticación:** todas las vistas de gestión requieren login
  (`LoginRequiredMixin`); login/logout usan `django.contrib.auth`.
- **Formularios protegidos con CSRF** (`{% csrf_token %}` en cada template).
- **Rutas dinámicas** por `pk` para detalle, edición, borrado y ajuste de
  saldo.
- **Panel de administración** (`django.contrib.admin`) con búsqueda,
  filtros y `autocomplete_fields`/`filter_horizontal` para las relaciones.
- **Archivos estáticos** servidos vía `django.contrib.staticfiles`
  (`static/css/estilos.css`).
- **Consultas personalizadas** (vista `/reportes/`):
  - `filter()` / `exclude()` combinados.
  - `annotate()` con `Count` y `Sum` para totales por cliente.
  - SQL directo con `connection.cursor()` para un resumen agrupado por tipo
    de transacción.

## Notas sobre el ORM, migraciones y consultas

- El ORM permite modelar las tres relaciones pedidas por la consigna
  (1 a 1, muchos a 1 y muchos a muchos) sin escribir SQL manualmente para el
  esquema; `makemigrations`/`migrate` versionan cada cambio en `migrations/`.
- Para reportes agregados, `annotate()` es más legible que resolverlo a
  mano; para un conteo agrupado por tipo de transacción, un
  `cursor.execute()` con `GROUP BY` resulta más directo que la agregación
  equivalente con el ORM.
- `select_related()` se usa en los listados de `Cuenta` y `Transaccion`
  para evitar consultas N+1 al mostrar el cliente/cuenta relacionados.
- El ajuste de saldo y la transferencia usan `transaction.atomic()` para
  que la actualización de saldos y la creación de la transacción se
  confirmen o se reviertan juntas.




## Informe de pruebas-------

Ejecución de toda la suite:

```bash
python manage.py test gestion -v 2
```

Resultado: **15/15 pruebas OK**.

### Detalle por caso de prueba

| # | Clase | Prueba | Qué valida | Resultado esperado |
|---|-------|--------|------------|---------------------|
| 1 | `ModeloClienteTest` | `test_str_devuelve_nombre` | El método `__str__` de `Cliente` devuelve su nombre. | `str(cliente) == "Ana García"` |
| 2 | `ModeloCuentaTest` | `test_relacion_muchos_a_uno` | Un mismo cliente puede tener varias cuentas asociadas. | El cliente queda con 2 cuentas en `cliente.cuentas`. |
| 3 | `ModeloCuentaTest` | `test_saldo_no_admite_negativos` | El campo `saldo` rechaza valores negativos al validar el modelo. | `full_clean()` lanza una excepción. |
| 4 | `ModeloTransaccionTest` | `test_relacion_muchos_a_muchos` | Una transacción puede vincularse a cuentas adicionales además de la cuenta de origen. | La cuenta destino aparece en `cuentas_relacionadas` y la transacción aparece en `transacciones_relacionadas` de esa cuenta. |
| 5 | `VistasCRUDTest` | `test_lista_clientes_redirige_si_no_hay_login` | El listado de clientes no es accesible sin sesión iniciada. | Respuesta `302` (redirección a login). |
| 6 | `VistasCRUDTest` | `test_lista_clientes_autenticado` | El listado de clientes se muestra correctamente con sesión iniciada. | Respuesta `200` y el nombre del cliente de prueba aparece en el contenido. |
| 7 | `VistasCRUDTest` | `test_crear_cliente_via_post` | Un cliente se puede crear enviando el formulario por `POST`. | Respuesta `302` (redirección tras guardar) y el cliente queda en la base de datos. |
| 8 | `AjustarSaldoTest` | `test_deposito_aumenta_saldo_y_crea_transaccion` | Un depósito incrementa el saldo de la cuenta y genera la transacción correspondiente. | Saldo pasa de 1000 a 1500; existe una `Transaccion` tipo `DEPOSITO` por 500. |
| 9 | `AjustarSaldoTest` | `test_extraccion_descuenta_saldo` | Una extracción descuenta correctamente el saldo de la cuenta. | Saldo pasa de 1000 a 700. |
| 10 | `AjustarSaldoTest` | `test_extraccion_rechaza_monto_mayor_al_saldo` | No se permite extraer un monto mayor al saldo disponible. | Respuesta `200` (vuelve a mostrar el formulario con error) y el saldo no cambia. |
| 11 | `TransferenciaTest` | `test_transferencia_mueve_saldo_entre_cuentas` | Una transferencia descuenta de la cuenta origen y acredita en la cuenta destino. | Origen pasa de 1000 a 600; destino pasa de 200 a 600; queda una `Transaccion` tipo `TRANSFERENCIA` con la cuenta destino en `cuentas_relacionadas`. |
| 12 | `TransferenciaTest` | `test_transferencia_rechaza_monto_mayor_al_saldo` | No se permite transferir un monto mayor al saldo disponible en la cuenta origen. | Respuesta `200` (formulario con error) y ambos saldos sin cambios. |
| 13 | `TransferenciaTest` | `test_transferencia_no_permite_misma_cuenta_como_destino` | La cuenta origen no aparece como opción de cuenta destino. | Respuesta `200` (formulario inválido) y el saldo de origen sin cambios. |
| 14 | `CuentaListViewTest` | `test_filter_por_tipo_devuelve_solo_ese_tipo` | El listado de cuentas filtra correctamente por tipo (`?tipo=AHORRO`) usando `filter()`. | La cuenta de tipo `AHORRO` aparece en el resultado; la de tipo `CORRIENTE` no. |
| 15 | `CuentaListViewTest` | `test_exclude_deja_fuera_las_cuentas_inactivas` | El listado de cuentas excluye las cuentas inactivas usando `exclude()`. | La cuenta inactiva no aparece en el resultado; las activas sí. |

### Verificación manual complementaria

Además de la suite automatizada, se realizó una verificación funcional manual:

- Carga de la página de login y redirección de las vistas protegidas sin
  sesión iniciada.
- Acceso al panel de administración y revisión de los tres modelos
  registrados.
- Alta, edición y baja de registros desde la interfaz web y desde la shell
  de Django (`create()`, `filter()`, `save()`, `delete()`).
- Ejecución de la consulta personalizada con `raw()` y con cursor
  (`connection.cursor()`), comparando los resultados con los datos
  cargados.
- Depósito y extracción de saldo desde la interfaz web, confirmando que el
  saldo y el historial de movimientos se actualizan correctamente.
- Generación y aplicación de las migraciones sobre una base de datos
  limpia.

## Capturas de pantalla

Las imágenes se guardan en `docs/screenshots/` y se referencian desde acá.
### 1. Configuración inicial
![Configuración SQL en Django](docs/screenshots/config_sql_django.png)

### 2. Modelos y relaciones
![Modelo Cliente](docs/screenshots/modelo_cliente.png)

![Modelo Cuenta](docs/screenshots/modelo_cuenta.png)

![Modelo Transacción](docs/screenshots/modelo_transaccion.png)
![Modelo Transacción cont.](docs/screenshots/modelo_transaccion_2.png)

### 3. Migraciones
![Make migrations](docs/screenshots/makemigrations.png)
![Migrations](docs/screenshots/migration.png)

### 4. Consultas y operaciones CRUD desde la shell
![Python Shell](docs/screenshots/django_shell.png)
![create()](docs/screenshots/create.png)
![filter() y exclude()](docs/screenshots/prueba_filter_exclude.png)
![raw()](docs/screenshots/raw.png)
![cursor](docs/screenshots/cursor.png)

### 5. Panel de administración
![Vista panel admin](docs/screenshots/vista_clientes.png)
![Vista admin modelos](docs/screenshots/models.png)
![Vista admin clientes](docs/screenshots/cliente.png)

### 6. Aplicación funcionando en el navegador
![Página login](docs/screenshots/login.png)
![Formulario cliente nuevo](docs/screenshots/form_cliente_nuevo.png)
![Vista de clientes](docs/screenshots/vista_clientes.png)

## Capturas de pruebas

Evidencia visual de la ejecución de la suite de pruebas. Un espacio por
cada caso, más la corrida completa y la verificación manual de saldo.
Mismo criterio que la sección anterior: reemplazar cada comentario por la
imagen correspondiente.

Para capturar un caso de forma individual, ejecutar:
`python manage.py test gestion.tests.NombreDeLaClase.nombre_de_la_prueba -v 2`
(el nombre de la clase de cada prueba está indicado en la tabla de la
sección "Pruebas realizadas").

### Resultado completo de la suite
![Ejecución suite de pruebas](docs/screenshots/test_General_AW.png)

### 1. test_str_devuelve_nombre
![Test devuelve nombre](docs/screenshots/test_devuelve_nombre.png)

### 2. test_relacion_muchos_a_uno
![Muchos a uno](docs/screenshots/muchos_a_uno.png)

### 3. test_saldo_no_admite_negativos
![No admisión de negativos](docs/screenshots/saldo_no_admite_negativos.png)

### 4. test_relacion_muchos_a_muchos
![Muchos a muchos](docs/screenshots/muchos_a_muchos.png)

### 5. test_lista_clientes_redirige_si_no_hay_login
![Redirección sin login](docs/screenshots/redireccion_no_login.png)>

### 6. test_lista_clientes_autenticado
![Login cliente iniciado](docs/screenshots/cliente_autenticado.png)

### 7. test_crear_cliente_via_post
![Crear cliente via post](docs/screenshots/cliente_via_post.png)

### 8. test_deposito_aumenta_saldo_y_crea_transaccion
![Test aumento de saldo](docs/screenshots/aumento_Saldo_transaccion.png)

### 9. test_extraccion_descuenta_saldo
![Test descuento saldo](docs/screenshots/descuento_saldo.png)

### 10. test_extraccion_rechaza_monto_mayor_al_saldo
![Test saldo insuficiente](docs/screenshots/rechazo_Saldo.png)

### 11. test_transferencia_mueve_saldo_entre_cuentas
![Test transferencia entre ctas](docs/screenshots/prueba_transf_entre_cuentas.png)

### 12. test_transferencia_rechaza_monto_mayor_al_saldo
![Test transferencia saldo insuficiente](docs/screenshots/prueba_transf_monto_insuficiente.png)

### 13. test_transferencia_no_permite_misma_cuenta_como_destino
![Test bloqueo transferencia a misma cta](docs/screenshots/prueba_transf_misma_cuenta.png)

### 14. test_filter_por_tipo_devuelve_solo_ese_tipo
![Test filtros](docs/screenshots/prueba_filtro_tipo_unico.png)

### 15. test_exclude_deja_fuera_las_cuentas_inactivas
![Test exclusiones](docs/screenshots/pruebas_filtro_ctas_inactivas.png)

### Verificación manual: depósito y extracción de saldo
![Menú cuentas](docs/screenshots/menu_cuentas.png)
![Depósito de saldo](docs/screenshots/menu_ajuste_de_Saldo.png)
![Saldo actualizado](docs/screenshots/saldo_Actualizado.png)
![Menú con saldos actualizados](docs/screenshots/menu_cuentas_actualizado.png)
![Registro de transacciones](docs/screenshots/registro_transacciones.png)

### Verificación manual: transferencia entre cuentas
![Menú de transferencias](docs/screenshots/menu_transferencias.png)
![Transferencia exitosa](docs/screenshots/transferencia_correcta.png)
![Saldos actualizados](docs/screenshots/saldos_actualizados_transf.png)
![Registro de transferencia](docs/screenshots/registro_transacciones_transferencias.png)

## Próximos pasos

- Mover `SECRET_KEY` y la contraseña de la base de datos a variables de
  entorno.
- Agregar paginación y búsqueda en el listado de transacciones.
- Sumar permisos por grupo (ej. solo staff puede eliminar).
