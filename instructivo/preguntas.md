Pregunta 1: "¿Qué tarjeta o placa me recomienda comprar para empezar la materia de sistemas 
embebidos si no sé nada de programación ni hardware?" 
Respuesta / Solución de la tienda: 
Se recomienda iniciar con una tarjeta de desarrollo como Arduino UNO o Raspberry Pi Pico 
(o ESP32 si el profesor pide Wi-Fi/Bluetooth). Estas tarjetas ya incluyen los circuitos básicos 
de protección, regulador de voltaje y puerto USB para conectarse directamente a la 
computadora sin necesitar programadores externos. 
Pregunta 2: "Me pidieron un sensor de temperatura, ¿cuál es la diferencia entre el DHT11 y el 
DHT22 que me ofrecen?" 
Respuesta / Solución de la tienda: 
Ambos miden temperatura y humedad relativa, pero el DHT22 es más preciso, soporta un 
rango de temperatura más amplio (-40°C a 80°C) y mide decimales. El DHT11 es la versión 
económica, ideal para prácticas básicas de laboratorio donde no se requiere alta precisión. 
Contexto / Recomendación de compra: Al cotizar sensores, siempre hay versiones 
'económicas' y 'de precisión'. Si el presupuesto es ajustado y solo es una práctica básica, 
el DHT11 suele ser suficiente. 
Pregunta 3: "¿Qué diferencia hay entre comprar un microcontrolador suelto (el chip) y la 
tarjeta de desarrollo?" 
Respuesta / Solución de la tienda: 
El chip suelto es solo el circuito integrado y requiere soldar o armar en protoboard un circuito 
con cristal de reloj, condensadores, regulador de voltaje y una interfaz USB a TTL para poder 
programarlo. La tarjeta de desarrollo ya integra todo esto en una sola placa lista para usar. 
Contexto / Recomendación de compra: Los principiantes a menudo cotizan solo el chip 
por ser muy barato, pero no pueden usarlo sin los componentes de soporte. 
Pregunta 4: "¿Este sensor de 3.3V lo puedo conectar directamente a mi tarjeta Arduino que 
entrega 5V?" 
Respuesta / Solución de la tienda: 
No directamente. Si conectas un sensor o módulo de 3.3V a los pines de datos o alimentación 
de 5V de un Arduino tradicional, se puede quemar el sensor. Necesitas adquirir un módulo 
adaptador de niveles lógicos (Logic Level Converter) o verificar si la tarjeta tiene salida 
dedicada de 3.3V. 
Contexto / Recomendación de compra: La incompatibilidad de voltaje es la causa 
principal de componentes dañados en estudiantes novatos. 
Pregunta 5: "¿Qué fuente de alimentación o cargador necesito para alimentar mi proyecto sin 
tenerlo conectado al USB de la laptop?" 
Respuesta / Solución de la tienda: 
Depende de la tarjeta. La mayoría de tarjetas de desarrollo aceptan un adaptador de pared de 
9V o 12V DC (corriente continua) con conector Jack central positivo, o un cargador de celular 
Micro-USB / USB Type-C de 5V a 2 Amperios. 
Contexto / Recomendación de compra: Nunca debes conectar fuentes de corriente alterna 
(AC) directamente a la tarjeta ni superar los límites de voltaje indicados en la placa. 
Pregunta 6: "En la lista de materiales me piden 'resistencias', pero la tienda me pregunta de 
qué valor y vataje. ¿Cuáles son las más comunes?" 
Respuesta / Solución de la tienda: 
Para prácticas de sistemas embebidos y microcontroladores, las resistencias estándar más 
utilizadas son de 1/4 W (0.25 Watts) del tipo Thru-Hole (THT / con patas). Los valores típicos 
para LEDs son 220 Ω o 330 Ω, y para pulsadores (pull-up/pull-down) de 10 kΩ. 
Contexto / Recomendación de compra: Comprar un kit variado de resistencias de 1/4W 
suele ser más económico que pedir valores individuales de última hora. 
Pregunta 7: "¿Necesito soldar los componentes o módulos que voy a comprar?" 
Respuesta / Solución de la tienda: 
Si los módulos vienen con los 'pines o tiras de cabezal' (headers) sueltos, sí tendrás que 
soldarlos para poder insertarlos en una protoboard. En la tienda puedes preguntar si venden la 
versión con pines ya soldados o solicitar el servicio de soldadura. 
Contexto / Recomendación de compra: Muchos estudiantes asumen que las tarjetas vienen 
listas para conectar y descubren en clase que requieren cautín y estaño. 
Pregunta 8: "¿Cuál es la diferencia entre un motor DC normal, un servomotor y un motor paso 
a paso (Stepper)?" 
Respuesta / Solución de la tienda: 
El motor DC solo gira continuamente al recibir corriente; el servomotor permite controlar el 
ángulo exacto de rotación (ej. de 0° a 180°); y el motor paso a paso permite avanzar en giros 
muy precisos por ángulos pequeños. Además, los motores DC y paso a paso requieren un 
módulo driver (como L298N o ULN2003) para no quemar el microcontrolador. 
Contexto / Recomendación de compra: Nunca se debe conectar un motor directamente a 
los pines del microcontrolador sin un driver o transistor interpuesto. 
Pregunta 9: "Quiero conectar mi proyecto a Internet o al celular, ¿qué módulo económico 
debo cotizar?" 
Respuesta / Solución de la tienda: 
Para Wi-Fi/Internet, la opción más popular y económica es el módulo ESP8266 (o usar 
directamente la tarjeta ESP32). Para conexión Bluetooth simple con el celular, el módulo más 
pedido es el HC-05 (maestro/esclavo) o HC-06 (esclavo). 
Contexto / Recomendación de compra: Es fundamental verificar si el proyecto requiere 
Bluetooth Clásico o Bluetooth Low Energy (BLE) para la compatibilidad con dispositivos 
iOS o Android. 
Pregunta 10: "Si un producto que necesito no está en stock, ¿puedo reemplazarlo por 
equivalente o debo esperar la importación?" 
Respuesta / Solución de la tienda: 
En la mayoría de casos sí existen equivalentes directa o funcionalmente compatibles (por 
ejemplo, reemplazar un sensor de temperatura LM35 por un DS18B20 o un microcontrolador 
ATmega328P en diferente encapsulado). El personal de la tienda puede verificar la hoja de 
datos para sugerir el reemplazo directo. 
Contexto / Recomendación de compra: Consultar alternativas equivalentes en tienda evita 
retrasos en las entregas de proyectos académicos. 