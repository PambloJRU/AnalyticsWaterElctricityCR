def numero_formato(n):
    sufijos = [
        (1000000000," B"),
        (1000000,"M"),
        (1000,"K")
    ]

    for valor, sufijo in sufijos:
        if n >= valor:
            resultado = n / valor

            if resultado.is_integer():
                return f"{int(resultado)}{sufijo}"
            
            return f"{resultado:.1f}{sufijo}"
    return str(n)