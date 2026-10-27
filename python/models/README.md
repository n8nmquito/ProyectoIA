# Modelos del clasificador de correos

El modelo final elegido es **modelo_clasificador_300.pkl**.
Los de 10, 100 y 200 se conservan para las pruebas de comparación.

Esta carpeta contiene cuatro versiones del clasificador de tickets de soporte TI.
Cada una aprendió de una cantidad diferente de correos. Las guardamos para
observar cómo cambian las predicciones al darle más ejemplos al sistema.

| Modelo | Correos usados | Su dataset en data/train/ |
|---|---:|---|
| modelo_clasificador_10.pkl | 10 | correos_10.json |
| modelo_clasificador_100.pkl | 100 | correos_100.json |
| modelo_clasificador_200.pkl | 200 | correos_200.json |
| modelo_clasificador_300.pkl | 300 | correos_300.json |

Todos reciben título y cuerpo y sugieren accesos, aplicaciones, infraestructura
u otros. También muestran una confianza estimada; ese porcentaje no garantiza
que la categoría sea correcta. El de 10 es una demostración con muy pocos datos.

Desde CMD en la carpeta del proyecto:

```cmd
python evaluar_nuevos.py --model 100
```

Cambia 100 por 10, 200 o 300 para elegir otra versión. Sin indicar modelo se
utiliza el de 300. Cada versión guarda sus resultados en una carpeta separada.
Los 25 correos de prueba están aparte en data/test y no se usaron para entrenar.

El manual completo está en docs/manual_usuario.md.

Para verificar los cuatro modelos y repetir las pruebas sin reentrenarlos:

```cmd
python -m src.evaluate_versions
```

El informe distingue entrenamiento, CV exploratoria y predicciones sin
etiquetas. El modelo de 10 tiene muy pocos ejemplos para la CV calibrada.
