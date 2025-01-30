from typing import Dict
import pandas as pd
import phonenumbers

def format_phone_number(parsed_number: phonenumbers.PhoneNumber) -> str:
    """Formatea un número telefónico al formato internacional"""
    return phonenumbers.format_number(
        parsed_number,
        phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )

def create_result_df(data: Dict) -> pd.DataFrame:
    """Crea un DataFrame formateado para mostrar resultados"""
    df = pd.DataFrame(
        data.items(),
        columns=['Campo', 'Valor']
    )
    return df.set_index('Campo')
