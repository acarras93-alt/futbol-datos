jugador = {
    "jugador_id": "DEMO-001",
    "nombre": "Jugador de ejemplo",
    "club": "Club de ejemplo",
    "agencia": "Agencia de ejemplo",
    "fin_contrato": "2027-06-30",
}

print("Jugador:", jugador["nombre"])
print("Club:", jugador["club"])

if jugador["agencia"] is None:
    print("Representante: dato pendiente")
else:
    print("Representante:", jugador["agencia"])
