# Integración Java / Web con Curva DLR

Para implementar esto en Java o un servidor estático, tienes dos caminos principales. Mi recomendación es el **Camino A**, ya que es mucho más robusto y fácil de mantener.

## Opción A: Puente Python -> JSON (Recomendado)
Mantén el script de Python corriendo como un "servicio" en segundo plano. Este script ahora genera un archivo `curva_dlr.json` cada minuto.

### Ventajas:
1.  **Simplicidad**: Java solo tiene que leer un archivo de texto (JSON), lo cual es trivial.
2.  **Servidor Estático**: Si subes ese JSON a un servidor (vía FTP o similar), cualquier sitio web puede leerlo con un simple `fetch()` sin necesidad de backend.
3.  **Memoria**: No sobrecargas Java con la lógica de WebSockets y autenticación de Matba Rofex.

### Ejemplo en Java para leer los datos:
```java
import java.io.FileReader;
import org.json.simple.JSONArray;
import org.json.simple.parser.JSONParser;

public class DlrConsumer {
    public static void main(String[] args) {
        JSONParser parser = new JSONParser();
        try {
            Object obj = parser.parse(new FileReader("curva_dlr.json"));
            JSONArray list = (JSONArray) obj;
            list.forEach(item -> System.out.println(item));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

---

## Opción B: Implementación Nativa en Java
Si quieres eliminar Python por completo, necesitas usar el **Primary Java Wrapper** o conectarte vía **FIX**.

### Requisitos:
1.  **Maven/Gradle**: Para gestionar dependencias.
2.  **Librería**: `primary-java-client` (oficial de Matba Rofex).

### Pasos:
1.  Configurar el cliente con tus credenciales del `.env`.
2.  Implementar un `MarketDataService` con un `Listener`.
3.  **Problema**: Java es mucho más verboso para manejar la expiración dinámica de instrumentos. Tendrías que recrear la lógica de `get_all_instruments` y parsear las fechas de los strings de los tickers manualmente cada vez.

---

## Mi opinión técnica
**No te compliques con Java para la captura.** Java es excelente para manejar transacciones y lógica pesada, pero para "scraping" o "polling" de APIs como esta, Python es 10 veces más rápido de programar y mantener.

**Estrategia ganadora:**
1.  Deja el script `servicio_dlr.py` corriendo (puedes usar un `screen` o `systemd` en Linux, o un `task scheduler` en Windows).
2.  Haz que Java lea el `curva_dlr.json`. 
3.  Si necesitas esto en una web estática, haz que el script suba el JSON a tu servidor cada minuto. No necesitas un servidor dinámico para mostrar precios si ya tienes el JSON actualizado.
