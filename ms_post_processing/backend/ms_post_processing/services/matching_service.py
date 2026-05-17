class MatchingService:

    def validar_match(self, nombre_detectado: str, nombre_catalogo: str, confianza: str) -> dict:
        nombre_final = nombre_catalogo if nombre_catalogo else nombre_detectado
        return {
            "nombre_final": nombre_final,
            "confianza_ajustada": confianza,
        }
