import pandas as pd
import numpy as np

def bpm6_wide_to_long(path_or_df, sep=',', encoding='utf-8'):
    """
    Convierte una tabla BPM6 en formato wide a formato long.
    path_or_df: ruta a CSV/TSV o un DataFrame ya cargado.
    sep: separador si path_or_df es ruta (',' o '\t').
    Retorna DataFrame con columnas: Año, Cuenta, Partida, Subpartida, Tipo de registro, Valor
    """
    # Cargar
    if isinstance(path_or_df, pd.DataFrame):
        df = path_or_df.copy()
    else:
        df = pd.read_csv(path_or_df, sep=sep, encoding=encoding, dtype=str)

    # Normalizar nombres de columnas: primera columna = 'Item', resto = años
    cols = list(df.columns)
    item_col = cols[0]
    year_cols = cols[1:]
    # Limpiar espacios en años
    year_cols = [c.strip() for c in year_cols]
    df.columns = [item_col] + year_cols

    # Listas de control (puedes ampliarlas según tu tabla)
    top_accounts = {'cuenta corriente', 'cuenta capital', 'cuenta financiera', 'errores y omisiones', 'errores y omisiones'}
    partida_keywords = {'bienes', 'servicios', 'ingreso primario', 'ingreso secundario', 'cuenta corriente', 'cuenta capital', 'cuenta financiera', 'cuenta de capital'}
    tipo_keys = {'crédito', 'credito', 'débito', 'debito', 'activos', 'pasivos', 'saldo'}

    # Variables de contexto
    current_cuenta = None
    current_partida = None
    current_subpartida = None

    rows_out = []

    def parse_value(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip().replace(',', '')  # quitar comas de miles
        if s == '':
            return np.nan
        try:
            return float(s)
        except:
            # intentar reemplazar paréntesis negativos: (123) -> -123
            if s.startswith('(') and s.endswith(')'):
                try:
                    return -float(s[1:-1].replace(',', ''))
                except:
                    return np.nan
            return np.nan

    for _, r in df.iterrows():
        label_raw = str(r[item_col]).strip()
        label = label_raw.lower()

        # Detectar cuentas principales
        if label in top_accounts or any(k in label for k in top_accounts):
            current_cuenta = label_raw
            current_partida = None
            current_subpartida = None
            # Si la fila tiene valores numéricos, interpretarlas como "Saldo" del nivel cuenta
            for y in year_cols:
                val = parse_value(r[y])
                if not np.isnan(val):
                    rows_out.append({
                        'Año': y,
                        'Cuenta': current_cuenta,
                        'Partida': None,
                        'Subpartida': None,
                        'Tipo de registro': 'Saldo',
                        'Valor': val
                    })
            continue

        # Si la etiqueta es una partida conocida
        if label in partida_keywords or any(label == k for k in partida_keywords):
            current_partida = label_raw
            current_subpartida = None
            # Si la fila tiene valores numéricos, interpretarlas como "Saldo" de la partida
            for y in year_cols:
                val = parse_value(r[y])
                if not np.isnan(val):
                    rows_out.append({
                        'Año': y,
                        'Cuenta': current_cuenta,
                        'Partida': current_partida,
                        'Subpartida': None,
                        'Tipo de registro': 'Saldo',
                        'Valor': val
                    })
            continue

        # Si la etiqueta es Crédito/Débito/Activos/Pasivos
        if label in tipo_keys or label.startswith('crédit') or label.startswith('credit') or label.startswith('débit') or label.startswith('debit') or label in ['activos', 'pasivos']:
            tipo = label_raw  # mantener acentos y mayúsculas originales
            for y in year_cols:
                val = parse_value(r[y])
                if not np.isnan(val):
                    rows_out.append({
                        'Año': y,
                        'Cuenta': current_cuenta,
                        'Partida': current_partida,
                        'Subpartida': current_subpartida,
                        'Tipo de registro': tipo,
                        'Valor': val
                    })
            continue

        # Si no cae en los anteriores, lo tratamos como subpartida (ej. Transporte, Viajes, etc.)
        # Actualizar subpartida y si tiene valores numéricos, guardarlos como Saldo de la subpartida
        current_subpartida = label_raw
        for y in year_cols:
            val = parse_value(r[y])
            if not np.isnan(val):
                # Si la fila tiene valores y no es Crédito/Débito, puede ser un saldo neto de la subpartida
                rows_out.append({
                    'Año': y,
                    'Cuenta': current_cuenta,
                    'Partida': current_partida,
                    'Subpartida': current_subpartida,
                    'Tipo de registro': 'Saldo',
                    'Valor': val
                })

    # Construir DataFrame final
    df_long = pd.DataFrame(rows_out, columns=['Año', 'Cuenta', 'Partida', 'Subpartida', 'Tipo de registro', 'Valor'])

    # Opcional: ordenar y limpiar
    df_long = df_long.dropna(subset=['Valor']).reset_index(drop=True)
    # Convertir Año a formato simple (por ejemplo "2023 (p)" se mantiene)
    df_long['Año'] = df_long['Año'].astype(str)
    # Reordenar columnas
    df_long = df_long[['Año', 'Cuenta', 'Partida', 'Subpartida', 'Tipo de registro', 'Valor']]

    return df_long

# Ejemplo de uso con un CSV
if __name__ == "__main__":
    # Si tu archivo está separado por tabulaciones usa sep='\t'
    # df_long = bpm6_wide_to_long("bpm6_wide.csv", sep=',')
    # Ejemplo con DataFrame construido a mano (fragmento)
    data = {
        'Item': ['Cuenta Corriente', 'Crédito', 'Débito', 'Bienes', 'Crédito', 'Débito', 'Servicios', 'Crédito', 'Débito', 'Transporte', 'Crédito', 'Débito'],
        '2022': ['1.154', '16.304', '15.149', '3.039', '13.795', '10.756', '-1.821', '888', '2.709', '', '200', '150'],
        '2023 (p)': ['-1.145', '13.534', '14.679', '261', '10.793', '10.532', '-1.347', '1.109', '2.456', '', '180', '140']
    }
    df_sample = pd.DataFrame(data)
    df_long = bpm6_wide_to_long(df_sample)
    print(df_long)