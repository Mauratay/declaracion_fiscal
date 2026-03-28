# Extractor Fiscal CFDI

Esta aplicación es una herramienta de código abierto desarrollada en Python y Streamlit que facilita la extracción de datos financieros de comprobantes fiscales (CFDI) en formato PDF. Su propósito es automatizar la suma de ingresos, retenciones de ISR y deducciones personales (gastos médicos) para asistir en la preparación de la declaración anual de impuestos en México.

## Características

* **Procesamiento de Nóminas:** Extrae la fecha de pago, el total de percepciones (ingresos brutos) y el ISR retenido de recibos de nómina en formato PDF.
* **Procesamiento de Facturas Médicas:** Identifica y extrae el monto total pagado en facturas correspondientes a honorarios médicos, dentales y gastos hospitalarios.
* **Privacidad por diseño:** El análisis y extracción de texto de los documentos se realiza estrictamente en la memoria local del equipo. Ningún dato financiero, fiscal o personal se transmite a servidores externos.
* **Exportación de datos:** Genera un reporte consolidado en formato CSV con el desglose por documento y los totales acumulados del ejercicio fiscal.

## Requisitos previos

* Python 3.8 o una versión superior instalada en el sistema.
* Gestor de paquetes `pip`.

## Instalación

1.  Clona este repositorio en tu equipo local mediante la terminal:
    ```bash
    git clone https://github.com/Mauratay/declaracion_fiscal.git
    cd declaracion_fiscal
    ```
2.  Instala las bibliotecas requeridas. Se recomienda el uso de un entorno virtual:
    ```bash
    pip install -r requirements.txt
    ```

## Uso de la aplicación

1.  Inicia la interfaz gráfica ejecutando el siguiente comando en la raíz del proyecto:
    ```bash
    streamlit run app.py
    ```
2.  El comando anterior abrirá automáticamente una pestaña en tu navegador web predeterminado (usualmente en la dirección `http://localhost:8501`).
3.  Selecciona y arrastra tus recibos de nómina (archivos `.pdf`) hacia la zona de carga designada en la primera columna.
4.  Selecciona y arrastra tus facturas médicas (archivos `.pdf`) hacia la zona de carga de la segunda columna.
5.  Marca la casilla de confirmación en la interfaz para habilitar el procesamiento.
6.  Haz clic en el botón **Procesar Archivos**.
7.  Visualiza el resumen de totales en pantalla y utiliza el botón correspondiente para descargar el reporte detallado en formato CSV.

## Licencia

Este proyecto se distribuye bajo los términos de la Licencia MIT. Esto permite su uso, copia, modificación, fusión, publicación, distribución, sublicencia y venta de copias del software sin restricciones comerciales.
