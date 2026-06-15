import polars as pl
import datetime

def inicializar_variables():
    # Definimos las 25 variables con su Unidad, Categoría y Fuente
    variables = [
        ("Crecimiento PIB Real", "%", "Core Doméstico", "INE"),
        ("PIB por Sector (Hidrocarburos y Minería)", "% Var", "Core Doméstico", "INE"),
        ("Inflación (IPC)", "% (Anual)", "Core Doméstico", "INE"),
        ("Déficit Fiscal (% del PIB)", "% del PIB", "Core Doméstico", "MEFP"),
        ("Balance Fiscal Primario", "% del PIB", "Core Doméstico", "MEFP"),
        ("Deuda Pública / PIB", "% del PIB", "Core Doméstico", "MEFP"),
        ("Reservas Internacionales (Brutas)", "Millones USD", "Core Doméstico", "BCB"),
        ("Cobertura de Reservas (Meses de Importación)", "Meses", "Core Doméstico", "BCB"),
        ("Tipo de Cambio Oficial (BOB/USD)", "BOB/USD", "Core Doméstico", "BCB"),
        ("Tipo de Cambio Real Efectivo (REER)", "Índice", "Core Doméstico", "BCB"),
        ("Balanza de Cuenta Corriente (% del PIB)", "% del PIB", "Core Doméstico", "BCB"),
        ("Balanza Comercial", "Millones USD", "Core Doméstico", "BCB"),
        ("Ingresos por Exportación de Gas Natural", "Millones USD", "Core Doméstico", "BCB"),
        ("Costo de Subsidio a Combustibles", "Millones USD", "Core Doméstico", "MEFP/YPFB"),
        ("Precio Gas Natural (Contratos Regionales)", "USD/MMBtu", "Externas Críticas", "Banco Mundial/YPFB"),
        ("Precio Petróleo (Brent)", "USD/Barril", "Externas Críticas", "Banco Mundial"),
        ("Precio del Zinc", "USD/TM", "Externas Críticas", "Banco Mundial"),
        ("Precio del Oro", "USD/Onza", "Externas Críticas", "Banco Mundial"),
        ("Crecimiento PIB - Brasil", "%", "Externas Críticas", "IBGE/BM"),
        ("Crecimiento PIB - Argentina", "%", "Externas Críticas", "INDEC/BM"),
        ("Crecimiento PIB - China", "%", "Externas Críticas", "NBS/BM"),
        ("Tasa de Fondos Federales EE.UU.", "%", "Externas Críticas", "Reserva Federal"),
        ("Prima de Riesgo Soberano (EMBI)", "Puntos (bps)", "Financieras y Riesgo", "JP Morgan"),
        ("Deuda Pública Externa", "Millones USD", "Financieras y Riesgo", "BCB"),
        ("Inversión Extranjera Directa (IED)", "Millones USD", "Financieras y Riesgo", "BCB")
    ]

    # Creamos el DataFrame con Polars incluyendo "Unidad"
    df = pl.DataFrame(
        variables, 
        schema=["Variable", "Unidad", "Categoria", "Fuente"], 
        orient="row"
    )
    
    # Añadimos columnas para el valor actual y la fecha de actualización
    df = df.with_columns([
        pl.lit(0.0).alias("Valor_Actual"),  # Inicia en 0 temporalmente
        pl.lit(datetime.date.today().strftime("%Y-%m-%d")).alias("Ultima_Actualizacion")
    ])

    # Guardamos en la carpeta de datos procesados
    df.write_csv("data/processed/top_25_macro_bolivia.csv")
    print("✅ Base de datos de 25 variables creada exitosamente con Unidades en data/processed/")

if __name__ == "__main__":
    inicializar_variables()