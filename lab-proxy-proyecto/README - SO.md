# Laboratorio de Proxy Reverso y Monitoreo

**Autores:** Samuel Perdomo Camargo y Juan Miguel Fajardo Valencia

## 1\. Descripción del proyecto

Este proyecto implementa una infraestructura basada en contenedores Docker para desplegar una aplicación web con un proxy inverso y balanceo de carga. Nginx recibe las solicitudes de los usuarios y las distribuye entre tres instancias de backend desarrolladas con Python y Flask.

La infraestructura también incorpora Prometheus para recopilar métricas, Grafana para visualizarlas, Nginx Prometheus Exporter para exponer las métricas de Nginx y cAdvisor para supervisar el uso de recursos de los contenedores.

## 2\. Arquitectura

Los servicios se ejecutan en una red Docker llamada `infra\_network`.

* **Nginx:** actúa como proxy inverso y distribuye las solicitudes entre `app1`, `app2` y `app3` mediante el grupo `backend\_pool`.
* **Backend (app1, app2 y app3):** tres instancias de una aplicación Flask. Cada instancia tiene un nombre identificador (`server 1`, `server 2` o `server 3`) y expone endpoints de aplicación y métricas.
* **Nginx Prometheus Exporter:** obtiene las estadísticas de Nginx mediante `stub\_status` y las convierte al formato que consulta Prometheus.
* **Prometheus:** recopila métricas de sí mismo, de los tres backends, del exportador de Nginx y de cAdvisor. El intervalo de recolección configurado es de 5 segundos.
* **cAdvisor:** recopila información sobre los recursos utilizados por los contenedores.
* **Grafana:** permite consultar y visualizar las métricas almacenadas en Prometheus.

Diagrama general
                    Usuario / navegador
                            |
                     http://localhost:8080
                            |
                          NGINX
                      (proxy inverso)
                            |
              +-------------+-------------+
              |             |             |
            app1          app2          app3
           Flask          Flask         Flask
              |             |             |
              +------ métricas /metrics --+
                            |
                      PROMETHEUS <----- Nginx Exporter
                            ^                 ^
                            |                 |
                         cAdvisor         Nginx
                            |
                         GRAFANA
                    (visualización)
```

## 3\. Tecnologías utilizadas

* Docker y Docker Compose.
* Python, Flask y Gunicorn para el backend.
* Nginx como proxy inverso y balanceador de carga.
* Prometheus para la recolección de métricas.
* Nginx Prometheus Exporter para las métricas de Nginx.
* cAdvisor para las métricas de los contenedores.
* Grafana para la visualización de métricas.
* k6 para las pruebas de carga.

## 4\. Requisitos previos

Antes de iniciar, se debe contar con:

1. Docker instalado y en ejecución (Docker Desktop en Windows o Docker Engine en Linux).
2. Docker Compose v2, disponible mediante el comando `docker compose`.
3. k6 instalado en el equipo anfitrión para ejecutar la prueba de carga.
4. Git, si se desea clonar el repositorio.

## 5\. Obtener e iniciar el proyecto

Clonar el repositorio y entrar en la carpeta del proyecto:

```bash
git clone https://github.com/juanfvalencia-dot/BALANCEO--CARGAS--NGNIX--SERVER/upload
cd lab-proxy-proyecto
```

Si ya se tiene descargada la carpeta del proyecto, basta con abrir una terminal en su directorio raíz, donde se encuentra `docker-compose.yml`.

Construir la imagen del backend e iniciar los servicios en segundo plano:

```bash
docker compose up --build -d
```

Consultar el estado de los contenedores:

```bash
docker compose ps
```

Para observar los registros de los servicios:

```bash
docker compose logs -f
```

Para salir de la visualización de registros, presionar `Ctrl + C`. Esto no detiene los contenedores.

## 6\. Acceso a los servicios

Con los contenedores en ejecución, los servicios publicados se pueden consultar desde el navegador del equipo anfitrión:

|Servicio|URL|Descripción|
|-|-|-|
|Aplicación web (Nginx)|http://localhost:8080|Punto de entrada de la aplicación y del balanceador.|
|Prometheus|http://localhost:9090|Consulta de métricas y estado de los targets.|
|Grafana|http://localhost:3000|Visualización de métricas mediante dashboards.|
|cAdvisor|http://localhost:8081|Interfaz de métricas de los contenedores.|

**Grafana:** el archivo `docker-compose.yml` habilita el acceso anónimo con rol administrador y desactiva el formulario de inicio de sesión. Por esta configuración, al abrir la URL no se solicita usuario ni contraseña.

## 7\. Verificar el balanceo de carga

1. Abrir http://localhost:8080 en el navegador.
2. Observar el nombre del servidor que aparece en la página (`server 1`, `server 2` o `server 3`).
3. Recargar la página varias veces. Nginx debe distribuir las solicitudes entre las tres instancias disponibles.

También se puede realizar varias solicitudes desde una terminal. En Linux o macOS:

```bash
for i in {1..12}; do
  curl -s http://localhost:8080/
  echo
 done
```

En PowerShell:

```powershell
1..12 | ForEach-Object { (Invoke-WebRequest http://localhost:8080).Content }
```

La respuesta HTML identifica el backend que atendió cada solicitud. También se puede consultar la cabecera `X-Backend` o `X-Upstream` con:

```bash
curl -i http://localhost:8080/
```

Otros endpoints disponibles en cada backend:

* `/health`: verifica el estado de la instancia.
* `/metrics`: expone las métricas de la aplicación en formato Prometheus. Este endpoint se consulta dentro de la red Docker y no tiene un puerto publicado directamente en el host.
* `/headers`: muestra las cabeceras recibidas por Flask.
* `/slow?ms=1000`: simula una respuesta demorada (el valor está expresado en milisegundos).

## 8\. Verificar Prometheus y Grafana

### Prometheus

1. Abrir http://localhost:9090.
2. Entrar a **Status > Targets** (o **Targets**, según la versión).
3. Comprobar que los objetivos configurados aparezcan en estado `UP`.

La configuración de `prometheus/prometheus.yml` contiene estos grupos de recolección:

* `prometheus`: el propio servidor Prometheus.
* `backends`: `app1:5000`, `app2:5000` y `app3:5000`.
* `nginx`: el exportador `nginx-exporter:9113`.
* `cadvisor`: `cadvisor:8080`.

En total, la configuración define **6 targets** si se cuenta el propio Prometheus: 1 de Prometheus, 3 backends, 1 exportador de Nginx y 1 cAdvisor. El dashboard exportado contiene un panel cuyo título indica “Targets arriba (esperado: 5)”; conviene revisar ese texto o la consulta del panel para que coincida con los seis targets configurados.

### Grafana

1. Abrir http://localhost:3000.
2. La fuente de datos **Prometheus** está configurada automáticamente mediante `grafana/provisioning/datasources/prometheus.yml`.
3. El proyecto incluye una exportación de un dashboard en `grafana/exports/`.
4. Si el dashboard no aparece en Grafana, importarlo desde **Dashboards > New > Import** y seleccionar el archivo JSON de esa carpeta. Verificar que la fuente de datos seleccionada sea **Prometheus**.

El dashboard exportado contiene paneles para observar, entre otros indicadores, los targets activos, las solicitudes por segundo, las conexiones activas, las respuestas 5xx, la latencia p95 por backend, el uso de CPU y la memoria por contenedor.

## 9\. Instalar y ejecutar la prueba de carga con k6

### Instalación de k6 en el host (Ubuntu / WSL)

k6 debe instalarse en el equipo anfitrión (host), no es necesario ejecutarlo dentro de un contenedor. En Ubuntu o WSL, se puede descargar e instalar el paquete oficial `.deb`:

```bash
wget https://github.com/grafana/k6/releases/download/v2.4.0/k6-v2.4.0-linux-amd64.deb
sudo dpkg -i k6-v2.4.0-linux-amd64.deb
rm -f k6-v2.4.0-linux-amd64.deb
```

Verificar que la instalación se haya realizado correctamente:

```bash
k6 version
```

> \*\*Nota:\*\* este paquete corresponde a Linux de arquitectura AMD64 (x86\_64). Si se utiliza otra arquitectura o sistema operativo, se debe descargar el paquete de k6 que corresponda desde sus canales oficiales.

### Ejecución de la prueba

El archivo `load-test.js`, ubicado en la raíz del proyecto, contiene una prueba que envía solicitudes HTTP al punto de entrada de Nginx (`http://localhost:8080/`). La prueba está configurada en tres etapas:

* **15 segundos:** incremento hasta 20 usuarios virtuales.
* **30 segundos:** carga sostenida de 50 usuarios virtuales.
* **15 segundos:** reducción hasta 0 usuarios virtuales.

Para ejecutarla, comprobar primero que la infraestructura esté activa y, desde la raíz del proyecto, ejecutar:

```bash
k6 run load-test.js
```

k6 mostrará en la terminal los resultados de la ejecución, incluidos los tiempos de respuesta y las comprobaciones del código HTTP 200. Mientras se ejecuta la prueba, se pueden consultar Prometheus y Grafana para observar el comportamiento de los servicios.

## 10\. Detener la infraestructura

Para detener y eliminar los contenedores y la red creados por Compose, ejecutar desde la raíz del proyecto:

```bash
docker compose down
```

Los volúmenes nombrados `prometheus\_data` y `grafana\_data` se conservan al utilizar ese comando, por lo que los datos persistentes no se eliminan.

> \*\*Advertencia:\*\* `docker compose down -v` también elimina los volúmenes y, por tanto, los datos persistentes de Prometheus y Grafana. Utilizarlo únicamente si se desea borrar esos datos.

## 11\. Estructura del proyecto

```text
lab-proxy-proyecto/
├── backend/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── grafana/
│   ├── exports/
│   └── provisioning/
│       └── datasources/
│           └── prometheus.yml
├── nginx/
│   └── nginx.conf
├── prometheus/
│   └── prometheus.yml
├── docker-compose.yml
├── load-test.js
└── README.md
```

\---

**Nota:** Las direcciones y los comandos de esta guía corresponden a la configuración incluida en este repositorio. Los puertos indicados utilizan los valores predeterminados definidos en `docker-compose.yml`.

