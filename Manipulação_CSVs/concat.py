import pandas as pd

# Ler os dois arquivos
df1 = pd.read_csv("")
df2 = pd.read_csv("")
df3 = pd.read_csv("")



# Concatenar (um embaixo do outro)
df_final = pd.concat([], ignore_index=True)

# Salvar o resultado
df_final.to_csv("", index=False)

print("Arquivos concatenados com sucesso!")


