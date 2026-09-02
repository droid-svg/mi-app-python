# -*- coding: utf-8 -*-
"""Contenido educativo: fonemas, sílabas, palabras, oraciones,
sinónimos, retos cognitivos, señas y vocabulario emocional."""

VOCALES = list("AEIOU")
CONSONANTES_BASICAS = list("MPSLNTDBFRC")

SILABAS = ["ma", "me", "mi", "mo", "mu", "pa", "pe", "pi", "po", "pu",
           "sa", "se", "si", "so", "su", "la", "le", "li", "lo", "lu"]

PALABRAS = [
    ("🐱", "gato"), ("🏠", "casa"), ("☀️", "sol"),
    ("🌙", "luna"), ("🐶", "perro"), ("🍎", "manzana"),
    ("🐟", "pez"), ("🌳", "árbol"), ("🚗", "carro"),
]

TRABALENGUAS = [
    "Tres tristes tigres tragaban trigo en un trigal.",
    "El cielo está enladrillado, ¿quién lo desenladrillará?",
    "Pablito clavó un clavito en la calva de un calvito.",
]

ORACIONES = [
    ["El", "niño", "lee", "un", "cuento"],
    ["Mi", "mamá", "prepara", "la", "comida"],
    ["El", "perro", "corre", "en", "el", "parque"],
]

COMPRENSION = [
    {
        "texto": "Ana tiene un gato blanco llamado Nube. A Nube le gusta dormir al sol.",
        "pregunta": "¿De qué color es Nube?",
        "opciones": ["Negro", "Blanco", "Gris"],
        "correcta": 1,
    },
    {
        "texto": "Luis desayuna fruta todas las mañanas antes de ir a la escuela.",
        "pregunta": "¿Qué hace Luis antes de la escuela?",
        "opciones": ["Duerme", "Desayuna fruta", "Juega fútbol"],
        "correcta": 1,
    },
]

SINONIMOS = [
    ("feliz", ["contento", "triste", "cansado"], 0),
    ("grande", ["pequeño", "enorme", "delgado"], 1),
    ("rápido", ["veloz", "lento", "quieto"], 0),
]

ANTONIMOS = [
    ("día", ["mañana", "noche", "tarde"], 1),
    ("frío", ["caliente", "fresco", "helado"], 0),
    ("alto", ["arriba", "bajo", "largo"], 1),
]

RETOS_COGNITIVOS = [
    {"pregunta": "¿Qué sigue? 2, 4, 6, __", "opciones": ["7", "8", "9"], "correcta": 1},
    {"pregunta": "El sol sale por el...", "opciones": ["Norte", "Este", "Oeste"], "correcta": 1},
    {"pregunta": "¿Cuántas patas tiene un perro?", "opciones": ["2", "4", "6"], "correcta": 1},
]

# Módulo 7: Lenguaje de señas / comunicación diaria
SEÑAS = [
    {"emoji": "🙋", "frase": "Necesito ayuda",
     "gesto": "Levanta la mano y muestra la palma abierta hacia el adulto.",
     "uso": "En clase o casa cuando algo cuesta o hay demasiado ruido."},
    {"emoji": "💧", "frase": "Quiero agua",
     "gesto": "Junta los dedos como si sostuvieras un vaso y llévalo a la boca.",
     "uso": "En comidas, recreo o durante actividades largas."},
    {"emoji": "🚻", "frase": "Necesito ir al baño",
     "gesto": "Cruza el dedo índice y medio y muéstralos al adulto.",
     "uso": "En el aula sin necesidad de hablar frente a otros."},
    {"emoji": "🍽️", "frase": "Tengo hambre",
     "gesto": "Lleva los dedos juntos a la boca varias veces.",
     "uso": "Antes de merienda o almuerzo."},
    {"emoji": "😴", "frase": "Me siento cansado",
     "gesto": "Apoya la mejilla en la mano con los ojos entrecerrados.",
     "uso": "Cuando la energía baja o el cuerpo pide pausa."},
    {"emoji": "🌪️", "frase": "Me siento abrumado",
     "gesto": "Cubre suavemente los oídos y respira profundo.",
     "uso": "Frente a ruido, luz o exceso de estímulos."},
    {"emoji": "😢", "frase": "Estoy triste",
     "gesto": "Desliza un dedo por la mejilla como una lágrima.",
     "uso": "Para nombrar la emoción sin necesidad de hablar."},
    {"emoji": "😊", "frase": "Estoy feliz",
     "gesto": "Sonríe y coloca las manos abiertas junto al rostro.",
     "uso": "Para celebrar logros pequeños."},
    {"emoji": "🙏", "frase": "Gracias",
     "gesto": "Toca los labios con la mano y llévala hacia adelante.",
     "uso": "Al recibir ayuda o algo que se necesitaba."},
    {"emoji": "🤲", "frase": "Por favor",
     "gesto": "Frota la palma abierta en círculos sobre el pecho.",
     "uso": "Al pedir algo con calma."},
    {"emoji": "🌞", "frase": "Buenos días",
     "gesto": "Saluda con la mano abierta desde la frente hacia adelante.",
     "uso": "Al llegar a casa o al aula."},
    {"emoji": "👋", "frase": "Adiós",
     "gesto": "Agita la mano suavemente de un lado a otro.",
     "uso": "Al despedirse sin sobresaltos."},
]

# Módulo 5 + 7: vocabulario emocional
EMOCIONES = [
    ("😊", "Feliz"), ("😢", "Triste"), ("😠", "Enojado"),
    ("😨", "Con miedo"), ("😌", "Tranquilo"), ("🥰", "Querido"),
    ("😴", "Cansado"), ("🌪️", "Abrumado"),
]


# Imagenes asociadas (assets/images/senas y assets/images/emociones)
SEÑAS_IMG = {
    "Necesito ayuda": "1.png",
    "Quiero agua": "2.png",
    "Necesito ir al baño": "3.png",
    "Tengo hambre": "4.png",
    "Me siento cansado": "5.png",
    "Me siento abrumado": "6.png",
    "Estoy triste": "7.png",
    "Estoy feliz": "10.png",
    "Gracias": "8.png",
    "Por favor": "11.png",
    "Buenos días": "12.png",
    "Adiós": "9.png",
}

EMOCIONES_IMG = {
    "Feliz": "1.png",
    "Triste": "2.png",
    "Enojado": "3.png",
    "Con miedo": "4.png",
    "Tranquilo": "5.png",
    "Querido": "6.png",
    "Cansado": "7.png",
    "Abrumado": "8.png",
}
