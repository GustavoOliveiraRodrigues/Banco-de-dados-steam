import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def carregar_dados(tabela_csv):
    df = pd.read_csv(tabela_csv)
    return df


# Carregamento de dados csv
df = carregar_dados(r'G:\Vscode projetos\steamdb\BigQuery\extracaoBQ.csv')
# Criando o DF para a seleção de colunas
busca_df = pd.DataFrame({
    "tipos": ['Tipo', 'Genero', 'Desenvolvedora', 'Publicadora']
})
# juntando os generos
df['genres'] = df['genres'].fillna('')
full_genres = set([genres for lista in df['genres'].str.split(', ')
                  for genres in lista])

# Variáveis
contagem_jogos = df['Nome'].count()

# layout 
    # Título
st.markdown("<h2 style='text-align: center;'>SteamDB</h2>", unsafe_allow_html=True)

    # Jogos
col1, col2, col3 = st.columns([4, 1, 4])

with col2:
    st.metric(label='Jogos', value=contagem_jogos)

    #Label Selecao
    # Seleção do tipo de busca
selection = busca_df['tipos'].unique()
selection_selecionado = st.selectbox("Tipo de busca", selection)

if selection_selecionado == "Tipo":
    app_type_selection = st.selectbox("Selecione um Tipo de Aplicativo", df['app_type'].unique())
    df_filtrado = df[df['app_type'] == app_type_selection]

elif selection_selecionado == "Genero":
    genres_selection = st.multiselect("Selecione os gêneros", list(full_genres))
    if genres_selection:
        df_filtrado = df[df['genres'].apply(lambda x: any(genre in x for genre in genres_selection))]
    else:
        df_filtrado = df

elif selection_selecionado == "Desenvolvedora":
    developer_selection = st.selectbox("Selecione uma Desenvolvedora", df['developer'].unique())
    df_filtrado = df[df['developer'] == developer_selection]

elif selection_selecionado == "Publicadora":
    publisher_selection = st.selectbox("Selecione uma Publicadora", df['publisher'].unique())
    df_filtrado = df[df['publisher'] == publisher_selection]

else:
    df_filtrado = df    


# Variaveis para os graficos
Colunas_desejadas = ['Nome', 'price', 'genres', 'developer', 'publisher']
df_colunas_desejadas = df_filtrado[Colunas_desejadas]

df_top10 = df_filtrado.nlargest(10, 'percentage_reviews').sort_values(by='percentage_reviews', ascending=False)


# Criação dos graficos
fig = px.bar(df_top10, x='Nome', y='percentage_reviews',
             labels={'percentage_reviews': 'Porcentagem de Reviews', 'Nome': 'Nome do Jogo'},
             title='TOP 10 Jogos Reviews', height=400)



#exibição 
st.dataframe(df_colunas_desejadas)
st.plotly_chart(fig)

   
    