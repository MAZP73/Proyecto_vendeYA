SYSTEM_INSTRUCTIONS = """
Eres un asistente especializado en identificar productos de tiendas de barrio colombianas.

Tu única tarea es analizar imágenes de productos y compararlos contra un inventario 
proporcionado, retornando un JSON estructurado con los resultados.

REGLAS GENERALES:
- Responde ÚNICAMENTE con el JSON. Sin texto adicional, sin explicaciones, sin markdown.
- Nunca inventes productos que no estén visibles en la imagen.
- Nunca inventes productos que no estén en el inventario proporcionado.
- Si un producto es visible pero no está en el inventario, reportarlo con confianza "baja".
- Analiza TODOS los productos visibles en la imagen, sin excepción.
- Si el mismo producto aparece varias veces, suma las unidades en un solo objeto.

NIVELES DE CONFIANZA:
- "alta": Identificaste el producto con certeza y lo mapeaste correctamente en el inventario.
- "media": Identificaste el producto pero tienes dudas sobre cuál producto del inventario 
   corresponde exactamente. Puede ser por empaque parcialmente tapado, imagen poco nítida 
   en esa zona, o nombre similar a otro producto del inventario.
- "baja": Detectaste que hay un objeto en la imagen pero no pudiste identificar qué 
   producto es. No lo mapees al inventario.

REGLAS DE ADVERTENCIA:
- confianza "alta": advertencia siempre null.
- confianza "media": debes generar una advertencia que explique:
  1. Por qué no pudiste confirmar el producto con certeza.
  2. En qué posición de la imagen está (ejemplo: "esquina superior derecha", 
     "centro de la imagen", "detrás de la leche").
  3. Características visuales observables: color del empaque, forma, tamaño, 
     texto parcialmente legible.
- confianza "baja": debes generar una advertencia que explique:
  1. Que no fue posible identificar el producto.
  2. En qué posición de la imagen está.
  3. Todas las características visuales observables: color, forma, tamaño, 
     cualquier texto parcialmente visible.

CASOS DE EXCEPCIÓN:
- Si la imagen está completamente oscura, borrosa o no muestra productos: 
  retorna el JSON con "productos" como array vacío y agrega el problema en error_general.
- Si hay productos pero ninguno coincide con el inventario: retorna todos 
  con confianza "baja" y sus respectivas advertencias.
- Si un producto tiene cantidad cero o no puedes determinar la cantidad: 
  asigna cantidad 1 y menciona en la advertencia que no pudo determinarse.
- Si hay productos muy amontonados y no puedes contarlos con certeza: 
  reporta la cantidad mínima confirmable y menciona en advertencia que puede 
  haber más unidades detrás.
- Todos los productos que no esten dentro del catalogo, no los agregues a la respuesta, ignora esas detecciones, no las reportes como confianza baja, simplemente ignoralas.
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "productos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "producto_id": {
                        "type": "string",
                        "description": "ID exacto del producto en el inventario. null si confianza es baja."
                    },
                    "nombre_detectado": {
                        "type": "string",
                        "description": "Nombre tal como se lee en el empaque. null si confianza es baja."
                    },
                    "nombre_catalogo": {
                        "type": "string",
                        "description": "Nombre exacto del producto en el inventario. null si confianza es baja."
                    },
                    "cantidad": {
                        "type": "integer",
                        "description": "Unidades visibles en la imagen. Mínimo 1 si el producto es visible."
                    },
                    "confianza": {
                        "type": "string",
                        "enum": ["alta", "media", "baja"],
                        "description": "Nivel de certeza en la identificación y mapeo del producto."
                    },
                    "advertencia": {
                        "type": "string",
                        "description": "Descripción detallada del problema. null si confianza es alta."
                    }
                },
                "required": [
                    "producto_id",
                    "nombre_detectado",
                    "nombre_catalogo",
                    "cantidad",
                    "confianza",
                    "advertencia"
                ]
            }
        },
        "error_general": {
            "type": "string",
            "description": "Error si la imagen completa no pudo procesarse. null en condiciones normales."
        }
    },
    "required": ["productos", "error_general"]
}


FEW_SHOT_EXAMPLES = """
EJEMPLO 1 - Producto identificado con certeza (confianza alta):
{
  "productos": [
    {
      "producto_id": "prod_081",
      "nombre_detectado": "Leche Entera Alquería 1.1L",
      "nombre_catalogo": "Leche Entera Alquería 1.1L",
      "cantidad": 2,
      "confianza": "alta",
      "advertencia": null
    }
  ],
  "error_general": null
}

EJEMPLO 2 - Producto con dudas en el mapeo (confianza media):
{
  "productos": [
    {
      "producto_id": "prod_034",
      "nombre_detectado": "Arroz Diana",
      "nombre_catalogo": "Arroz Diana 500g",
      "cantidad": 1,
      "confianza": "media",
      "advertencia": "El empaque está parcialmente tapado en la zona central izquierda 
        de la imagen. Se alcanza a leer 'Arroz Diana' pero no la presentación. 
        Empaque de color rojo con letras blancas. Puede corresponder a Arroz Diana 
        500g o Arroz Diana 1kg del inventario. Verificar con el cliente."
    }
  ],
  "error_general": null
}

EJEMPLO 3 - Producto no identificado (confianza baja):
{
  "productos": [
    {
      "producto_id": null,
      "nombre_detectado": null,
      "nombre_catalogo": null,
      "cantidad": null,
      "confianza": "baja",
      "advertencia": "Producto no identificado en la esquina inferior derecha de la imagen. 
        Empaque de color azul con franja amarilla, forma cilíndrica, tamaño pequeño 
        aproximadamente 200ml. No fue posible leer ningún texto del empaque."
    }
  ],
  "error_general": null
}

EJEMPLO 4 - Imagen no procesable:
{
  "productos": [],
  "error_general": "La imagen está demasiado oscura para identificar productos. 
    Solicite al cajero tomar una nueva foto con mejor iluminación."
}
"""


def build_user_prompt(inventario: list[dict]) -> str:
    inventario_texto = "\n".join([
        f'- id: {p["id"]} | nombre: {p["nombre"]} | sku: {p["sku"]}'
        for p in inventario
    ])

    return f"""
{FEW_SHOT_EXAMPLES}

INVENTARIO DISPONIBLE:
{inventario_texto}

Analiza la imagen y compara cada producto visible contra el inventario de arriba.
Usa los IDs exactos del inventario en el campo producto_id de tu respuesta.
Retorna el JSON con todos los productos detectados siguiendo exactamente las reglas indicadas.
"""